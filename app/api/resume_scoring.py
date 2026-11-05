# Web addresses for Agent 1 (the resume scorer)
import json
import os
import time

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.agents.resume_scoring.agent import score_cv
from app.agents.resume_scoring.safety import evidence_is_real, find_trick_lines
from app.api.files import upload_to_text

# All addresses in this file start with /resume-scoring
router = APIRouter(prefix="/resume-scoring", tags=["Agent 1: Resume scoring"])

LEVELS = ["Junior", "Mid", "Senior", "Team Lead"]


# Turns the skills list into text for the prompt, one skill per line
def skills_to_text(skills):
    lines = []
    for skill in skills:
        lines.append(f"- {skill['skill']} ({skill['type']}, needed level {skill['required_level']} of 5)")
    return "\n".join(lines)


# Scores one CV for one job.
# It uses Form and File (not JSON), because it receives files
@router.post("/score")
def score(
    position: str = Form(...),
    skills: str = Form(...),
    cv_file: UploadFile = File(...),
    job_text: str = Form(""),
    job_file: UploadFile | None = File(None),
):
    if position not in LEVELS:
        raise HTTPException(status_code=400, detail=f"Level must be one of: {', '.join(LEVELS)}")

    # skills comes as JSON text: '[{"skill": "Python", "type": "Must-have", "required_level": 3}]'
    skill_list = json.loads(skills)
    if not skill_list:
        raise HTTPException(status_code=400, detail="Add at least one skill.")

    # The job post: the uploaded file wins, else the pasted text
    if job_file is not None:
        job_post = upload_to_text(job_file, [".md", ".txt", ".pdf", ".docx"])
    else:
        job_post = job_text
    if not job_post.strip():
        raise HTTPException(status_code=400, detail="Add a job post: upload a file or paste the text.")

    resume_text = upload_to_text(cv_file, [".pdf", ".docx"])
    if not resume_text.strip():
        raise HTTPException(status_code=422, detail="Needs Manual Review: the CV has no text. It may be a scanned picture.")

    # Layer 1: find trick lines, so HR can see them
    trick_lines = find_trick_lines(resume_text)

    start = time.time()
    result = score_cv(position, job_post, skills_to_text(skill_list), resume_text)
    seconds = round(time.time() - start, 1)

    # score_cv gives back None when all 3 AI tries fail
    if result is None:
        raise HTTPException(status_code=502, detail="The AI failed 3 times. Needs Manual Review. Try again in a minute.")

    # Layer 3: check that every proof line is really in the CV
    proof_checks = [{"line": line, "found": evidence_is_real(line, resume_text)} for line in result.proof_lines]

    # model_dump() turns the Pydantic result into a normal dictionary, and FastAPI sends it as JSON
    return {
        **result.model_dump(),
        "trick_lines": trick_lines,
        "proof_checks": proof_checks,
        "seconds": seconds,
        "model": os.environ["LLM_MODEL"],
        "cv_characters": len(resume_text),
    }
