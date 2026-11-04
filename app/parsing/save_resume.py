from app.core.database.database import run_sql
from app.parsing.reader import check_file, read_resume


def save_resume(name, email, file_path):
    file_status = check_file(file_path)
    if file_status != "OK":
        return file_status

    # A broken or locked file can't be read, so a human must check it
    try:
        resume_text = read_resume(file_path)
    except Exception as error:
        resume_text = ""
        if "Password" in str(error):
            print("Needs Manual Review: PDF is locked")

    if resume_text.strip():
        status = "Resume Received"
    else:
        status = "Needs Manual Review"

    run_sql(
        """
        INSERT INTO candidates (name, email, resume_path, resume_text, current_status)
        VALUES (:name, :email, :resume_path, :resume_text, :status)
        """,
        {
            "name": name,
            "email": email,
            "resume_path": file_path,
            "resume_text": resume_text,
            "status": status,
        },
    )
    return status
