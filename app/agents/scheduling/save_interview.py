# Saves Agent 3's work in the database (the interviews table), and sends the emails after HR says yes:
# the invite, a "your interview has moved" email, and a "your interview is cancelled" email
import json
import os
from datetime import datetime

from dotenv import load_dotenv
from redmail import gmail
from sqlalchemy import text

from app.core.audit import add_audit_event
from app.core.database.database import engine, get_one, run_sql
from app.core.status import change_status

load_dotenv()

# My Gmail login, from .env (the same as the score email). No keys = MOCK
gmail.username = os.environ.get("SMTP_EMAIL", "")
gmail.password = os.environ.get("SMTP_APP_PASSWORD", "")


# Sends one email to the candidate and logs it. Gives back "Sent", "MOCK" or "Failed"
def send_email(candidate_id, subject, body, email_name):
    candidate = get_one("SELECT email FROM candidates WHERE id = :id", {"id": candidate_id})
    if candidate is None:
        raise ValueError(f"Candidate {candidate_id} not found")
    if not gmail.username:
        status = "MOCK"
    else:
        try:
            gmail.send(subject=subject, receivers=[candidate.email], text=body)
            status = "Sent"
        except Exception:
            status = "Failed"
    run_sql("""
        INSERT INTO communication_logs (candidate_id, channel, template_name, delivery_status, sent_at)
        VALUES (:id, 'Email', :name, :status, CURRENT_TIMESTAMP)
    """, {"id": candidate_id, "name": email_name, "status": status})
    return status


# One interview row. Stops with a clear message if it doesn't exist
def get_interview(interview_id):
    interview = get_one("SELECT candidate_id, send_status, confirmed_slot FROM interviews WHERE id = :id", {"id": interview_id})
    if interview is None:
        raise ValueError(f"Interview {interview_id} not found")
    return interview


# The agent found times and wrote an email: save them as a proposal. Nothing is sent yet
def save_proposal(candidate_id, slots, email, settings, hr_email):
    with engine.begin() as conn:
        interview_id = conn.execute(text("""
            INSERT INTO interviews (candidate_id, interviewer_id, proposed_slots, timezone, meeting_details, email_draft)
            VALUES (:candidate_id, :interviewer_id, :slots, :timezone, :meeting, :email)
            RETURNING id
        """), {
            "candidate_id": candidate_id,
            "interviewer_id": slots[0]["interviewer_id"],
            "slots": json.dumps(slots),
            "timezone": settings["timezone"],
            "meeting": f"{settings['meeting_type']}, {settings['interview_minutes']} minutes",
            "email": json.dumps(email),
        }).scalar_one()
    change_status(candidate_id, "Interview Proposed")
    add_audit_event(hr_email, "Interview times proposed", "candidate", candidate_id, f"{len(slots)} times")
    return interview_id


# Every interview with its candidate, job and interviewer, newest first
def list_interviews():
    with engine.begin() as conn:
        rows = conn.execute(text("""
            SELECT interviews.*, candidates.name AS candidate_name, candidates.email AS candidate_email,
                   jobs.title AS job_title, employees.name AS interviewer_name
            FROM interviews
            JOIN candidates ON candidates.id = interviews.candidate_id
            JOIN jobs ON jobs.id = candidates.job_id
            LEFT JOIN employees ON employees.id = interviews.interviewer_id
            ORDER BY interviews.id DESC
        """)).mappings().all()
    return [dict(row) for row in rows]


# HR says yes: send the invite for the picked time. Gives back "Sent", "MOCK", "Failed" or "Already sent".
# "Failed" keeps the interview as a proposal, so HR can press Resend
def send_invite(interview_id, slot, subject, body, hr_email):
    interview = get_interview(interview_id)
    if interview.send_status in ("Sent", "MOCK"):
        return "Already sent"

    status = send_email(interview.candidate_id, subject, body, "Interview invite")
    # HR's choice and the email are saved even if sending failed, so Resend uses the same ones
    booked = status != "Failed"
    run_sql("""
        UPDATE interviews
        SET confirmed_slot = :slot, interviewer_id = :interviewer_id, email_draft = :email, approval_status = 'Approved',
            send_status = :status, status = :interview_status, sent_at = :sent_at
        WHERE id = :id
    """, {"id": interview_id, "slot": slot["start"], "interviewer_id": slot["interviewer_id"],
          "email": json.dumps({"subject": subject, "body": body}), "status": status,
          "interview_status": "Scheduled" if booked else "Proposed",
          "sent_at": datetime.now().isoformat(" ", "seconds") if booked else None})
    if booked:
        change_status(interview.candidate_id, "Interview Scheduled")
    add_audit_event(hr_email, "Interview invite", "candidate", interview.candidate_id, f"{status}: {slot['start']}")
    return status


# Move: send the update email first. Only if it went out, the new time is saved (a failed send changes nothing, so HR just tries again)
def move_interview(interview_id, slot, subject, body, hr_email):
    interview = get_interview(interview_id)
    status = send_email(interview.candidate_id, subject, body, "Interview moved")
    if status != "Failed":
        run_sql("UPDATE interviews SET confirmed_slot = :slot, interviewer_id = :interviewer_id WHERE id = :id",
                {"id": interview_id, "slot": slot["start"], "interviewer_id": slot["interviewer_id"]})
        add_audit_event(hr_email, "Interview moved", "candidate", interview.candidate_id,
                        f"{interview.confirmed_slot} → {slot['start']} ({status})")
    return status


# Cancel: send the cancel email first. Only if it went out, the interview is cancelled and the candidate is closed (with the reason)
def cancel_interview(interview_id, reason, subject, body, hr_email):
    interview = get_interview(interview_id)
    status = send_email(interview.candidate_id, subject, body, "Interview cancelled")
    if status != "Failed":
        run_sql("UPDATE interviews SET status = 'Cancelled' WHERE id = :id", {"id": interview_id})
        change_status(interview.candidate_id, "Closed")
        add_audit_event(hr_email, "Interview cancelled", "candidate", interview.candidate_id, f"{reason} ({status})")
    return status
