# The calling agent without a phone: pretend calls, call problems → HR to-dos, no answer → call again → human,
# the test-number safety list, and the ElevenLabs webhook (with a real signature check).
# Test database only:
#   $env:DATABASE_URL = "sqlite:///./tests/test.db"; uv run python -m app.core.database.init_db
#   uv run python tests/calling_test.py
import hashlib
import hmac
import json
import os
import sys
import time
from pathlib import Path

sys.path[:0] = [str(Path(__file__).parents[1]), str(Path(__file__).parents[1] / "frontend")]
sys.stdout.reconfigure(encoding="utf-8")
os.environ.pop("ELEVENLABS_PHONE_NUMBER_ID", None)        # no Twilio number = pretend calls
os.environ["TEST_PHONE_NUMBERS"] = "+923001234567"
os.environ["ELEVENLABS_WEBHOOK_SECRET"] = "test-secret"

from fastapi.testclient import TestClient
from streamlit.testing.v1 import AppTest

import app.api.webhooks as webhooks
from app.agents.script_agent.agent import call_candidate, calls_are_real, is_test_number
from app.agents.script_agent.save_call import save_call_result, save_call_started, save_no_answer, save_pretend_call
from app.api.main import app
from app.core.candidates import approve_for_calling
from app.core.database.database import get_one, run_sql
from app.core.hr_tasks import list_tasks

results = []


def check(name, ok, info=""):
    results.append(("PASS" if ok else "FAIL", name, str(info)[:100]))


def status(cid):
    return get_one("SELECT current_status FROM candidates WHERE id = :id", {"id": cid}).current_status


def new_candidate(cid, phone="+923001234567"):
    run_sql("INSERT INTO candidates (id, job_id, name, email, phone, current_status) VALUES (:id, 1, :n, :e, :p, 'Scored (HR Review)')",
            {"id": cid, "n": f"Person {cid}", "e": f"p{cid}@example.com", "p": phone})
    approve_for_calling(cid, "hr")


run_sql("INSERT INTO jobs (title, job_description, level, work_type, scoring_weights) VALUES ('Junior Python Developer','x','Junior','Remote','f')")
ANSWERS = {"consent_given": True, "available_date_time": "Tuesday afternoon", "previous_job": "Intern",
           "reason_for_shift": "To grow", "wants_human": False, "needs_other_way": False}

# ---------- 1. Pretend call ----------
check("1 no phone number in .env → pretend calls", not calls_are_real())
new_candidate(1)
check("1 pretend call saved", save_pretend_call(1, ANSWERS, "hr") == "Saved" and status(1) == "Screening Completed (HR Review)")
summary = get_one("SELECT summary, candidate_availability FROM screenings WHERE candidate_id = 1")
check("1 marked MOCK, answers saved", summary.summary.startswith("MOCK") and summary.candidate_availability == "Tuesday afternoon")

# ---------- 2. Call problems → HR to-dos ----------
new_candidate(2)
save_pretend_call(2, {**ANSWERS, "consent_given": False, "wants_human": True, "needs_other_way": True}, "hr")
titles = [t["title"] for t in list_tasks("Open")]
check("2 said no to recording → to-do", "The candidate said no to the recorded call" in titles)
check("2 wants a human → to-do", "The candidate wants to talk to a human" in titles)
check("2 other language / no phone → to-do", "The candidate needs another language or can't do a phone call" in titles)

# ---------- 3. Saved only once ----------
conversation = get_one("SELECT conversation_id FROM screenings WHERE candidate_id = 1").conversation_id
check("3 the same result twice → saved once", save_call_result(1, conversation, {**ANSWERS, "summary": "x"}, "hr") == "Already saved")

# ---------- 4. No answer → call again → a human ----------
new_candidate(3)
save_call_started(3, "call-3a", "hr")
check("4 1st no answer → try again", save_no_answer(3, "call-3a", "hr") == (1, 2) and status(3) == "Screening Pending")
save_call_started(3, "call-3b", "hr")
check("4 2nd no answer (limit 2) → Needs Manual Review + to-do", save_no_answer(3, "call-3b", "hr") == (2, 2)
      and status(3) == "Needs Manual Review" and "Couldn't reach the candidate after 2 calls" in [t["title"] for t in list_tasks("Open")])

# ---------- 5. Safety: real calls only to test numbers ----------
check("5 test number allowed (spaces ok)", is_test_number("+92 300 1234567"))
check("5 other number refused", not is_test_number("+923339999999"))
try:
    call_candidate("+923339999999", "Real Person", "Job")
    check("5 call_candidate refuses a real number", False)
except ValueError as e:
    check("5 call_candidate refuses a real number (before any call)", True, e)

# ---------- 6. The webhook ----------
client = TestClient(app)


def post(event, secret="test-secret"):
    body = json.dumps(event)
    stamp = str(int(time.time()))
    signature = hmac.new(secret.encode(), f"{stamp}.{body}".encode(), hashlib.sha256).hexdigest()
    return client.post("/webhooks/elevenlabs", content=body, headers={"elevenlabs-signature": f"t={stamp},v0={signature}"})


new_candidate(4)
save_call_started(4, "call-4", "hr")
webhooks.get_call_result = lambda conversation_id: {**ANSWERS, "summary": "Real call summary"}   # pretend ElevenLabs
check("6 health", client.get("/health").json() == {"status": "ok"})
check("6 wrong signature → 401", post({"type": "post_call_transcription", "data": {"conversation_id": "call-4"}}, "wrong").status_code == 401)
check("6 no signature → 401", client.post("/webhooks/elevenlabs", content="{}").status_code == 401)
check("6 not my call → ignored", post({"type": "post_call_transcription", "data": {"conversation_id": "nope"}}).json()["saved"] is False)
answer = post({"type": "post_call_transcription", "data": {"conversation_id": "call-4"}}).json()
check("6 call ended → saved by itself", answer == {"saved": True, "result": "Saved"} and status(4) == "Screening Completed (HR Review)", answer)
check("6 sent twice → saved once", post({"type": "post_call_transcription", "data": {"conversation_id": "call-4"}}).json()["result"] == "Already saved")
new_candidate(5)
save_call_started(5, "call-5", "hr")
answer = post({"type": "call_initiation_failure", "data": {"conversation_id": "call-5", "failure_reason": "no-answer"}}).json()
check("6 no answer → saved as no answer", answer["result"] == "No answer, try 1 of 2", answer)

# ---------- 7. The page shows the pretend-call form ----------
new_candidate(6)
page = AppTest.from_file(str(Path(__file__).parents[1] / "frontend" / "pages" / "candidates" / "candidates.py"), default_timeout=60)
page.session_state.user = {"name": "HR", "email": "hr@test", "role": "HR"}
page.session_state.blind = False
page.session_state.picked_candidate = 6
page.run()
page.text_input(key="mock_when").input("Monday morning")
[b for b in page.button if b.label == "Save pretend call"][0].click().run()
check("7 page: pretend call form works", not page.exception and status(6) == "Screening Completed (HR Review)", page.exception)

for result, name, info in results:
    print(f"{result}  {name}  ->  {info}")
print(f"{sum(r == 'PASS' for r, _, _ in results)} PASS, {sum(r == 'FAIL' for r, _, _ in results)} FAIL")
