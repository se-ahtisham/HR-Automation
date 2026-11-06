# Saves the script agent's calls in the database (the screenings table), and turns call problems into HR to-dos
import json
from uuid import uuid4

from app.core.audit import add_audit_event
from app.core.database.database import get_one, run_sql
from app.core.hr_tasks import add_task
from app.core.settings import get_settings
from app.core.status import change_status

# Call problems a human must sort out: the answer's name → (the to-do, its type)
PROBLEMS = {
    "wants_human": ("The candidate wants to talk to a human", "Human requested"),
    "needs_other_way": ("The candidate needs another language or can't do a phone call", "Language"),
}


# How many times this candidate was called
def call_tries(candidate_id):
    row = get_one("SELECT COUNT(*) AS n FROM screenings WHERE candidate_id = :id", {"id": candidate_id})
    return row.n if row else 0


# The call has started: remember its id, so the answers can be found later
def save_call_started(candidate_id, conversation_id, hr_email):
    run_sql("""
        INSERT INTO screenings (candidate_id, conversation_id, call_status, call_tries, call_time)
        VALUES (:candidate_id, :conversation_id, 'Calling', :tries, CURRENT_TIMESTAMP)
    """, {"candidate_id": candidate_id, "conversation_id": conversation_id, "tries": call_tries(candidate_id) + 1})
    # A call again (after no answer) keeps the status it already has
    candidate = get_one("SELECT current_status FROM candidates WHERE id = :id", {"id": candidate_id})
    if candidate and candidate.current_status == "Approved for Calling":
        change_status(candidate_id, "Screening Pending")
    add_audit_event(hr_email, "Call started", "candidate", candidate_id)


# The call has ended: save the answers and the summary (never the transcript), and add an HR to-do for each problem.
# Saved only once, even if the button and the webhook both bring the result
def save_call_result(candidate_id, conversation_id, result, hr_email):
    call = get_one("SELECT call_status FROM screenings WHERE conversation_id = :id", {"id": conversation_id})
    if call is None or call.call_status == "Done":
        return "Already saved"

    run_sql("""
        UPDATE screenings
        SET call_status = 'Done', consent_status = :consent, candidate_availability = :availability,
            answers = :answers, summary = :summary
        WHERE conversation_id = :conversation_id
    """, {
        "consent": "Yes" if result["consent_given"] else "No",
        "availability": result["available_date_time"],
        "answers": json.dumps({"previous_job": result["previous_job"], "reason_for_shift": result["reason_for_shift"]}),
        "summary": result["summary"],
        "conversation_id": conversation_id,
    })
    change_status(candidate_id, "Screening Completed (HR Review)")

    if result["consent_given"] is False:
        add_task("The candidate said no to the recorded call", "Other", candidate_id, "Offer another way, like an email.", hr_email)
    for answer, (title, task_type) in PROBLEMS.items():
        if result.get(answer):
            add_task(title, task_type, candidate_id, "From the screening call.", hr_email)
    add_audit_event(hr_email, "Call result saved", "candidate", candidate_id)
    return "Saved"


# Nobody answered (or it was busy). HR may call again, up to "Call tries" in Settings. Then a human takes over
def save_no_answer(candidate_id, conversation_id, hr_email):
    run_sql("UPDATE screenings SET call_status = 'No answer' WHERE conversation_id = :id", {"id": conversation_id})
    tries, limit = call_tries(candidate_id), get_settings()["call_tries"]
    if tries >= limit:
        change_status(candidate_id, "Needs Manual Review")
        add_task(f"Couldn't reach the candidate after {tries} calls", "Other", candidate_id, "Try an email instead.", hr_email)
    add_audit_event(hr_email, "Call not answered", "candidate", candidate_id, f"try {tries} of {limit}")
    return tries, limit


# A pretend call (MOCK): HR types the answers, and they are saved like a real call
def save_pretend_call(candidate_id, answers, hr_email):
    conversation_id = f"mock-{uuid4().hex[:8]}"
    save_call_started(candidate_id, conversation_id, hr_email)
    return save_call_result(candidate_id, conversation_id, {**answers, "summary": "MOCK: a pretend call, typed by HR."}, hr_email)
