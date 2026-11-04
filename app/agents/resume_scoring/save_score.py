# Save results to database.
import json
import os

from app.core.database.database import run_sql


# Saves Agent 1's result for one candidate and one job
def save_score(candidate_id, job_id, result, trick_lines):
    part_scores = {
        "skills": result.skills,
        "experience": result.experience,
        "projects": result.projects,
        "education": result.education,
        "leadership": result.leadership,
        "other": result.other,
    }

    run_sql(
        """
        INSERT INTO resume_evaluations
            (candidate_id, job_id, total_score, criterion_scores, strengths,
             weak_points, missing_skills, proof_lines, warnings, model_version)
        VALUES
            (:candidate_id, :job_id, :total_score, :criterion_scores, :strengths,
             :weak_points, :missing_skills, :proof_lines, :warnings, :model_version)
        """,
        {
            "candidate_id": candidate_id,
            "job_id": job_id,
            "total_score": result.total_score,
            "criterion_scores": json.dumps(part_scores),
            "strengths": json.dumps(result.strengths),
            "weak_points": json.dumps(result.weak_points),
            "missing_skills": json.dumps(result.missing_skills),
            "proof_lines": json.dumps(result.proof_lines),
            "warnings": json.dumps(trick_lines),
            "model_version": os.environ["LLM_MODEL"],
        },
    )
