# Saves the script agent's work in the database (the screenings table)
import json

from app.core.audit import add_audit_event
from app.core.database.database import run_sql
from app.core.status import change_status


# The call has started: remember its id, so I can get the answers later
def save_call_started(candidate_id, conversation_id, hr_email):
    run_sql(
        """
        INSERT INTO screenings (candidate_id, conversation_id, call_status, call_tries, call_time)
        VALUES (:candidate_id, :conversation_id, 'Calling', 1, CURRENT_TIMESTAMP)
        """,
        {"candidate_id": candidate_id, "conversation_id": conversation_id},
    )
    change_status(candidate_id, "Screening Pending")
    add_audit_event(hr_email, "Call started", "candidate", candidate_id)


# The call has ended: save the answers and the summary. Never the full transcript
def save_call_result(candidate_id, conversation_id, result, hr_email):
    run_sql(
        """
        UPDATE screenings
        SET call_status = 'Done', consent_status = :consent, candidate_availability = :availability,
            answers = :answers, summary = :summary
        WHERE conversation_id = :conversation_id
        """,
        {
            "consent": "Yes" if result["consent_given"] else "No",
            "availability": result["available_date_time"],
            "answers": json.dumps({"previous_job": result["previous_job"], "reason_for_shift": result["reason_for_shift"]}),
            "summary": result["summary"],
            "conversation_id": conversation_id,
        },
    )
    change_status(candidate_id, "Screening Completed (HR Review)")
    add_audit_event(hr_email, "Call result saved", "candidate", candidate_id)
