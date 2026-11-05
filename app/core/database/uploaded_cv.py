# Saves a CV that a candidate uploaded: keeps the file, reads its text, and adds the candidate to the database
from pathlib import Path
from uuid import uuid4

from sqlalchemy import text

from app.core.audit import add_audit_event
from app.core.database.database import engine
from app.agents.resume_scoring.reader import FileProblem, upload_to_text

# Uploaded CV files are kept here. The folder is in .gitignore, because CVs hold personal data
CV_FOLDER = Path(__file__).parents[3] / "data" / "cvs"


# Gives back (candidate_id, status). A wrong file type or a too-big file raises FileProblem and is not saved
def save_uploaded_cv(job_id, name, email, file_name, data):
    # A locked or broken file is still saved, but a human must check it
    try:
        resume_text = upload_to_text(file_name, data, [".pdf", ".docx"])
    except FileProblem as problem:
        if not str(problem).startswith("Needs Manual Review"):
            raise
        resume_text = ""
    status = "Resume Received" if resume_text.strip() else "Needs Manual Review"

    # A random file name, so two CVs called "cv.pdf" never overwrite each other
    CV_FOLDER.mkdir(parents=True, exist_ok=True)
    file_path = CV_FOLDER / f"{uuid4().hex}{Path(file_name).suffix.lower()}"
    file_path.write_bytes(data)

    # RETURNING id gives back the new candidate's id from the same INSERT
    with engine.begin() as conn:
        candidate_id = conn.execute(
            text("""
                INSERT INTO candidates (job_id, name, email, resume_path, resume_text, current_status)
                VALUES (:job_id, :name, :email, :resume_path, :resume_text, :status)
                RETURNING id
            """),
            {
                "job_id": job_id,
                "name": name.strip(),
                "email": email.strip().lower(),
                "resume_path": str(file_path),
                "resume_text": resume_text,
                "status": status,
            },
        ).scalar_one()

    # Never put the CV text in the audit log
    add_audit_event(email.strip().lower(), "CV uploaded", "candidate", candidate_id, f"status: {status}")
    return candidate_id, status
