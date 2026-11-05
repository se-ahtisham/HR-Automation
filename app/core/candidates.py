# Candidates for the HR pages: the list with scores and call results, and HR's decisions
import json
from pathlib import Path

from sqlalchemy import text

from app.core.audit import add_audit_event
from app.core.database.database import engine
from app.core.status import change_status


# Every candidate with their job, newest score and newest call. Best score first
def list_candidates():
    with engine.begin() as conn:
        rows = conn.execute(text("""
            SELECT candidates.id, candidates.name, candidates.email, candidates.phone, candidates.current_status,
                   candidates.resume_text, candidates.job_id,
                   jobs.title AS job_title, jobs.level,
                   resume_evaluations.total_score, resume_evaluations.criterion_scores, resume_evaluations.skill_scores,
                   resume_evaluations.strengths, resume_evaluations.weak_points, resume_evaluations.missing_skills,
                   resume_evaluations.proof_lines, resume_evaluations.warnings, resume_evaluations.model_version,
                   screenings.conversation_id, screenings.call_status, screenings.consent_status,
                   screenings.candidate_availability, screenings.answers, screenings.summary
            FROM candidates
            JOIN jobs ON jobs.id = candidates.job_id
            LEFT JOIN resume_evaluations ON resume_evaluations.id = (
                SELECT MAX(id) FROM resume_evaluations WHERE resume_evaluations.candidate_id = candidates.id
            )
            LEFT JOIN screenings ON screenings.id = (
                SELECT MAX(id) FROM screenings WHERE screenings.candidate_id = candidates.id
            )
            ORDER BY resume_evaluations.total_score DESC
        """)).mappings().all()
    return [dict(row) for row in rows]


# Turns a saved score back into the dictionary the score view shows (the same shape as score_with_checks)
def saved_score(candidate):
    return {
        **json.loads(candidate["criterion_scores"]),
        "total_score": candidate["total_score"],
        "skill_scores": json.loads(candidate["skill_scores"]),
        "strengths": json.loads(candidate["strengths"]),
        "weak_points": json.loads(candidate["weak_points"]),
        "missing_skills": json.loads(candidate["missing_skills"]),
        "proof_checks": [{"line": line, "found": line in (candidate["resume_text"] or "")}
                         for line in json.loads(candidate["proof_lines"])],
        "trick_lines": json.loads(candidate["warnings"] or "[]"),
        "model": candidate["model_version"],
        "seconds": None,
    }


# HR stop #1: HR approves the candidate, so the script agent can call them
def approve_for_calling(candidate_id, hr_email):
    change_status(candidate_id, "Approved for Calling")
    add_audit_event(hr_email, "Approved for calling", "candidate", candidate_id)


# HR stop #1: HR declines the candidate. The reason is saved in the audit log
def decline(candidate_id, reason, hr_email):
    change_status(candidate_id, "Closed")
    add_audit_event(hr_email, "Declined", "candidate", candidate_id, reason)


# Deletes a candidate for good: their rows in every table, and their CV file.
# The tables that point to candidates go first, because the foreign keys don't allow a row to point to nothing
def delete_candidate(candidate_id, hr_email):
    with engine.begin() as conn:
        resume_path = conn.execute(text("SELECT resume_path FROM candidates WHERE id = :id"), {"id": candidate_id}).scalar()
        conn.execute(text("DELETE FROM resume_evaluations WHERE candidate_id = :id"), {"id": candidate_id})
        conn.execute(text("DELETE FROM screenings WHERE candidate_id = :id"), {"id": candidate_id})
        conn.execute(text("DELETE FROM interviews WHERE candidate_id = :id"), {"id": candidate_id})
        conn.execute(text("DELETE FROM communication_logs WHERE candidate_id = :id"), {"id": candidate_id})
        conn.execute(text("DELETE FROM hr_tasks WHERE candidate_id = :id"), {"id": candidate_id})
        conn.execute(text("DELETE FROM candidates WHERE id = :id"), {"id": candidate_id})

    # The CV file has personal data, so it goes too
    if resume_path:
        Path(resume_path).unlink(missing_ok=True)
    add_audit_event(hr_email, "Candidate deleted", "candidate", candidate_id)
