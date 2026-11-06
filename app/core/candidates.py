# Candidates for the HR pages: the list with scores and call results, and HR's decisions
import json
from pathlib import Path

from sqlalchemy import text

from app.core.audit import add_audit_event
from app.core.database.database import engine, get_one, run_sql
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


# Fix: HR changes a candidate's details (the CV reader can get them wrong). Gives back an error message, or None when saved
def fix_candidate(candidate_id, name, email, phone, hr_email):
    if not name.strip():
        return "Please write the name."
    if email.strip() and ("@" not in email or "." not in email):
        return "Please write a real email address."
    # One person applies only once, so 2 candidates can't share an email
    if email.strip() and get_one("SELECT id FROM candidates WHERE email = :email AND id != :id",
                                 {"email": email.strip().lower(), "id": candidate_id}):
        return "Another candidate already has this email."
    run_sql(
        "UPDATE candidates SET name = :name, email = :email, phone = :phone WHERE id = :id",
        {"id": candidate_id, "name": name.strip(), "email": email.strip().lower(), "phone": phone.strip()},
    )
    # Never put the details themselves in the audit log
    add_audit_event(hr_email, "Details fixed", "candidate", candidate_id)
    return None


# Privacy: deletes candidates older than the "keep data" days (Settings, 90 by default). Gives back how many
def delete_old_candidates():
    row = get_one("SELECT keep_data_days FROM scheduling_settings WHERE id = 1")
    days = row.keep_data_days if row else 90
    with engine.begin() as conn:
        old_ids = conn.execute(text("SELECT id FROM candidates WHERE created_at < datetime('now', :age)"),
                               {"age": f"-{days} days"}).scalars().all()
    for candidate_id in old_ids:
        delete_candidate(candidate_id, f"auto clean-up (older than {days} days)")
    return len(old_ids)
