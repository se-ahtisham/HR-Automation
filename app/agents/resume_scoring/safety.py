from pydantic import BaseModel, Field

# Words that try to give orders to the AI
SUSPICIOUS_PHRASES = [
    "ignore all previous instructions",
    "ignore previous instructions",
    "ignore the above",
    "ignore your rules",
    "disregard your instructions",
    "forget your instructions",
    "you must give",
    "give this candidate a score",
    "give me a score",
    "score of 100",
    "mark every skill as",
    "this is the best candidate",
    "you are now",
    "new instructions",
    "system prompt",
]


# The answer the AI must give back
class CVResult(BaseModel):
    total_score: int = Field(ge=0, le=100)
    skills: int = Field(ge=0, le=5)
    experience: int = Field(ge=0, le=5)
    projects: int = Field(ge=0, le=5)
    education: int = Field(ge=0, le=5)
    leadership: int = Field(ge=0, le=5)
    other: int = Field(ge=0, le=5)
    strengths: list[str]
    weak_points: list[str]
    missing_skills: list[str]
    proof_lines: list[str]


# Layer 1: finds trick phrases, so HR can see them
def find_trick_lines(resume_text):
    text = resume_text.lower()
    return [phrase for phrase in SUSPICIOUS_PHRASES if phrase in text]


# Layer 3: a proof line must really be in the CV.
# Spaces and line breaks are ignored, because PDFs break lines in odd places
def evidence_is_real(evidence, resume_text):
    evidence = " ".join(evidence.lower().split())
    resume_text = " ".join(resume_text.lower().split())
    return evidence in resume_text
