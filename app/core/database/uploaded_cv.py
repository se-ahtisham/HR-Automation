# Saves a CV that a candidate uploaded: keeps the file, reads its text, and adds the candidate to the database
from pathlib import Path
from uuid import uuid4

from sqlalchemy import text

from app.core.audit import add_audit_event
from app.core.database.database import engine, get_one
from app.agents.resume_scoring.contact import read_contact
from app.agents.resume_scoring.reader import FileProblem, upload_to_text

# Uploaded CV files are kept here. The folder is in .gitignore, because CVs hold personal data
CV_FOLDER = Path(__file__).parents[3] / "data" / "cvs"


# Gives back (candidate_id, status). The name, email and phone are read from the CV.
# A wrong file type or a too-big file raises FileProblem and is not saved
def save_uploaded_cv(job_id, file_name, data):
    # A locked or broken file is still saved, but a human must check it
    try:
        resume_text = upload_to_text(file_name, data, [".pdf", ".docx"])
    except FileProblem as problem:
        if not str(problem).startswith("Needs Manual Review"):
            raise
        resume_text = ""
    status = "Resume Received" if resume_text.strip() else "Needs Manual Review"

    # HR doesn't type the name, email and phone: they come from the CV
    contact = read_contact(resume_text)
    name = contact.name or "Name not found"

    # One person applies only once, for one job. Their CV is scored only for the job HR picked
    if contact.email:
        old = get_one("""
            SELECT candidates.id, jobs.title FROM candidates
            JOIN jobs ON jobs.id = candidates.job_id
            WHERE candidates.email = :email
        """, {"email": contact.email.lower()})
        if old:
            raise FileProblem(f"This person already applied for {old.title} (Candidate #{old.id}). It was not scored again.")

    # A random file name, so two CVs called "cv.pdf" never overwrite each other
    CV_FOLDER.mkdir(parents=True, exist_ok=True)
    file_path = CV_FOLDER / f"{uuid4().hex}{Path(file_name).suffix.lower()}"
    file_path.write_bytes(data)

    # RETURNING id gives back the new candidate's id from the same INSERT
    with engine.begin() as conn:
        candidate_id = conn.execute(
            text("""
                INSERT INTO candidates (job_id, name, email, phone, resume_path, resume_text, current_status)
                VALUES (:job_id, :name, :email, :phone, :resume_path, :resume_text, :status)
                RETURNING id
            """),
            {
                "job_id": job_id,
                "name": name,
                "email": contact.email.lower(),
                "phone": contact.phone,
                "resume_path": str(file_path),
                "resume_text": resume_text,
                "status": status,
            },
        ).scalar_one()

    # Never put the CV text in the audit log
    add_audit_event("upload", "CV uploaded", "candidate", candidate_id, f"status: {status}")
    return candidate_id, status
