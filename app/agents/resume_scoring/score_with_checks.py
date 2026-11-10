# Runs Agent 1 together with the safety checks, and gives back one dictionary for the web page
import os
import time

from app.agents.resume_scoring.agent import score_cv
from app.agents.resume_scoring.safety import evidence_is_real, find_trick_lines


# Turns the skills list into text for the prompt, one skill per line
def skills_to_text(skills):
    lines = []
    for skill in skills:
        lines.append(f"- {skill['skill']} ({skill['type']}, needed level {skill['required_level']} of 5)")
    return "\n".join(lines)


# Gives back the result as a dictionary, or None when the AI failed 3 times
def score_with_checks(position, skills, job_post, resume_text):
    # Layer 1: find trick lines, so HR can see them
    trick_lines = find_trick_lines(resume_text)

    start = time.time()
    result = score_cv(position, job_post, skills_to_text(skills), resume_text)
    seconds = round(time.time() - start, 1)

    if result is None:
        return None

    # Layer 3: check that every proof line is really in the CV
    proof_checks = [{"line": line, "found": evidence_is_real(line, resume_text)} for line in result.proof_lines]

    return {
        **result.model_dump(),
        "trick_lines": trick_lines,
        "proof_checks": proof_checks,
        "seconds": seconds,
        "model": os.environ["LLM_MODEL"],
    }
