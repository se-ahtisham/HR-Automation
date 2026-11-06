# Scores a candidate's CV for one saved job:
# save the candidate and file -> run Agent 1 with this job's level, skills and post -> save the score -> move the status
from app.agents.resume_scoring.safety import CVResult
from app.agents.resume_scoring.save_score import save_score
from app.agents.resume_scoring.score_with_checks import score_with_checks
from app.core.audit import add_audit_event
from app.core.blind import clean_cv
from app.core.database.database import get_one
from app.core.database.uploaded_cv import save_uploaded_cv
from app.core.status import change_status


# The job's skills in the shape Agent 1 and the result view use
def job_skills(job):
    return [{"skill": s["name"], "type": s["skill_type"], "required_level": s["required_level"]} for s in job["skills"]]


# Gives back (candidate_id, result). result is None when a human must check the CV.
# A wrong file type or a too-big file raises FileProblem before anything is saved
def score_cv_for_job(job, file_name, data, hr_email):
    candidate_id, status = save_uploaded_cv(job["id"], file_name, data)
    if status == "Needs Manual Review":
        return candidate_id, None

    # Blind Review Mode: the AI only sees a cleaned copy (no name, email, phone or links), so it judges the skills
    cv = get_one("SELECT name, resume_text FROM candidates WHERE id = :id", {"id": candidate_id})
    result = score_with_checks(job["level"], job_skills(job), job["job_description"], clean_cv(cv.resume_text, cv.name))

    # The AI failed 3 times, so a human must check this CV
    if result is None:
        change_status(candidate_id, "Needs Manual Review")
        return candidate_id, None

    # save_score wants the CVResult object, so I build it back from the result dictionary
    cv_result = CVResult.model_validate({key: result[key] for key in CVResult.model_fields})
    save_score(candidate_id, job["id"], cv_result, result["trick_lines"])
    change_status(candidate_id, "Scored (HR Review)")
    add_audit_event(hr_email, "CV scored", "candidate", candidate_id, f"score: {result['total_score']}")
    return candidate_id, result
