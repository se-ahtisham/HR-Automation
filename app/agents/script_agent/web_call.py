# The script agent in the browser (16 Nov): no phone number needed.
#   1. HR approves for calling, then clicks "Send the link": send_call_link emails the candidate a secret link
#   2. The candidate opens it: the Ask questions page finds them with candidate_by_token and shows the ElevenLabs agent
#   3. The agent asks the 4 questions. My app gives it {{candidate_id}}, so the talk can be found later
#   4. save_web_call finds the talk on ElevenLabs, gets the answers + summary, and saves them in the screenings table
# Switched on by APP_URL in .env (my app's web address, like https://nexora-hire.streamlit.app)
import os
import secrets

from app.agents.script_agent.agent import client, get_call_result
from app.agents.script_agent.prompts import CALL_LINK_EMAIL, CALL_LINK_SUBJECT
from app.agents.script_agent.save_call import save_call_result, save_call_started
from app.agents.scheduling.save_interview import send_email
from app.core.audit import add_audit_event
from app.core.database.database import get_one, run_sql
from app.core.status import change_status

# The statuses in which the candidate's link still works (before the answers are saved)
LINK_OPEN = ("Approved for Calling", "Screening Pending")


def web_calls_on():
    return bool(os.environ.get("APP_URL"))


# The candidate's link. The token is made once, so sending again gives the same link
def make_link(candidate_id):
    row = get_one("SELECT access_token FROM candidates WHERE id = :id", {"id": candidate_id})
    token = row.access_token if row and row.access_token else secrets.token_urlsafe(24)
    run_sql("UPDATE candidates SET access_token = :token WHERE id = :id", {"token": token, "id": candidate_id})
    return f"{os.environ['APP_URL'].rstrip('/')}/?token={token}"


# Emails the link. Gives back "Sent", "MOCK" (no Gmail keys) or "Failed"
def send_call_link(candidate_id, hr_email):
    candidate = get_one("""
        SELECT c.name, c.current_status, j.title AS job_title
        FROM candidates c JOIN jobs j ON j.id = c.job_id
        WHERE c.id = :id
    """, {"id": candidate_id})
    link = make_link(candidate_id)
    body = CALL_LINK_EMAIL.format(name=candidate.name, job_title=candidate.job_title, link=link)
    status = send_email(candidate_id, CALL_LINK_SUBJECT.format(job_title=candidate.job_title), body, "Call link")
    if status != "Failed" and candidate.current_status == "Approved for Calling":
        change_status(candidate_id, "Screening Pending")
    add_audit_event(hr_email, "Call link sent", "candidate", candidate_id, status)
    return status


# The candidate who owns this link, or None for a wrong link
def candidate_by_token(token):
    if not token:
        return None
    row = get_one("""
        SELECT c.id, c.name, c.current_status, j.title AS job_title
        FROM candidates c JOIN jobs j ON j.id = c.job_id
        WHERE c.access_token = :token
    """, {"token": token})
    return dict(row._mapping) if row else None


# The newest talk of this candidate on ElevenLabs, found by the candidate_id my page gave the agent. None = no talk yet
def find_web_call(candidate_id, look_at=20):
    page = client.conversational_ai.conversations.list(agent_id=os.environ["ELEVENLABS_AGENT_ID"], page_size=look_at)
    for summary in page.conversations:                      # newest first
        call = client.conversational_ai.conversations.get(conversation_id=summary.conversation_id)
        data = call.conversation_initiation_client_data
        variables = (data.dynamic_variables if data else None) or {}
        if str(variables.get("candidate_id")) == str(candidate_id):
            return call.conversation_id
    return None


# Finds the talk and saves the answers. Gives back "Saved", "Already saved", "No talk yet" or "Not finished"
def save_web_call(candidate_id, who):
    conversation_id = find_web_call(candidate_id)
    if conversation_id is None:
        return "No talk yet"
    result = get_call_result(conversation_id)
    if result is None or result.get("no_answer"):
        return "Not finished"
    # The first time a talk is found it has no screenings row yet, so one is made
    if get_one("SELECT id FROM screenings WHERE conversation_id = :id", {"id": conversation_id}) is None:
        save_call_started(candidate_id, conversation_id, who)
    return save_call_result(candidate_id, conversation_id, result, who)
