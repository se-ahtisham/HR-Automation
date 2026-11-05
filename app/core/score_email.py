# The CV Match Score email: after scoring, HR clicks "Send score to candidate".
# Jinja2 fills in the design (score_email.html), and Red Mail sends it with Gmail
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader
from redmail import gmail

from app.core.audit import add_audit_event
from app.core.database.database import get_one, run_sql

load_dotenv()

# autoescape=True: text from the CV can't break the HTML
templates = Environment(loader=FileSystemLoader(Path(__file__).parent), autoescape=True)

# My Gmail login, from .env. SMTP_APP_PASSWORD is a Gmail "app password", not my normal password
gmail.username = os.environ.get("SMTP_EMAIL", "")
gmail.password = os.environ.get("SMTP_APP_PASSWORD", "")


# Builds the email for one candidate from the saved score. Gives back (email, subject, html)
def write_score_email(candidate_id):
    row = get_one("""
        SELECT candidates.name, candidates.email, jobs.title, resume_evaluations.total_score,
               resume_evaluations.strengths, resume_evaluations.weak_points, resume_evaluations.missing_skills
        FROM candidates
        JOIN jobs ON jobs.id = candidates.job_id
        JOIN resume_evaluations ON resume_evaluations.candidate_id = candidates.id
        WHERE candidates.id = :id
        ORDER BY resume_evaluations.id DESC
    """, {"id": candidate_id})

    if row is None:
        raise ValueError(f"Candidate {candidate_id} has no score yet")

    html = templates.get_template("score_email.html").render(
        name=row.name,
        job_title=row.title,
        score=row.total_score,
        strengths=json.loads(row.strengths),
        weak_points=json.loads(row.weak_points),
        missing_skills=json.loads(row.missing_skills),
    )
    return row.email, f"Your CV Match Score for {row.title}: {row.total_score}/100", html


# Sends the email once. Gives back "Sent", "MOCK", "Failed", "Already sent" or "No email".
# No Gmail keys in .env = MOCK: the send is saved, but nothing is really sent
def send_score_email(candidate_id, hr_email):
    if get_one("SELECT id FROM communication_logs WHERE candidate_id = :id AND delivery_status IN ('Sent', 'MOCK')",
               {"id": candidate_id}):
        return "Already sent"

    to_email, subject, html = write_score_email(candidate_id)
    if not to_email:
        return "No email"

    if not gmail.username:
        status = "MOCK"
    else:
        try:
            gmail.send(subject=subject, receivers=[to_email], html=html)
            status = "Sent"
        except Exception:
            status = "Failed"

    # Every send is written down, so it is never sent twice
    run_sql("""
        INSERT INTO communication_logs (candidate_id, channel, template_name, delivery_status, sent_at)
        VALUES (:id, 'Email', 'CV Match Score', :status, CURRENT_TIMESTAMP)
    """, {"id": candidate_id, "status": status})
    add_audit_event(hr_email, "CV Match Score email", "candidate", candidate_id, status)
    return status
