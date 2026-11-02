# Save Rusume text in Databse

from app.core.database.database import run_sql
from app.parsing.reader import read_resume


def save_resume(name, email, file_path):
    resume_text = read_resume(file_path)

    run_sql(
        """
        INSERT INTO candidates (name, email, resume_path, resume_text)
        VALUES (:name, :email, :resume_path, :resume_text)
        """,
        {
            "name": name,
            "email": email,
            "resume_path": file_path,
            "resume_text": resume_text,
        },
    )
