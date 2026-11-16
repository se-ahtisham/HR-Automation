# The browser talk (16 Nov): HR sends the secret link → the candidate opens the Ask questions page → the answers
# are found on ElevenLabs and saved. ElevenLabs is pretended here (no minutes used), except one read-only check.
# Test database only:
#   $env:DATABASE_URL = "sqlite:///./tests/test.db"; uv run python -m app.core.database.init_db
#   uv run python tests/web_call_test.py
import os
import sys
from pathlib import Path

sys.path[:0] = [str(Path(__file__).parents[1]), str(Path(__file__).parents[1] / "frontend")]
sys.stdout.reconfigure(encoding="utf-8")
os.environ["APP_URL"] = "https://nexora-test.streamlit.app"     # browser talks on
os.environ["SMTP_EMAIL"] = ""                                  # MOCK email: set BEFORE importing the email code

from streamlit.testing.v1 import AppTest

import app.agents.script_agent.web_call as web_call
from app.agents.script_agent.web_call import candidate_by_token, save_web_call, send_call_link, web_calls_on
from app.core.candidates import approve_for_calling
from app.core.database.database import get_one, run_sql

ROOT = Path(__file__).parents[1]
results = []
ANSWERS = {"consent_given": True, "available_date_time": "Monday 3 pm", "previous_job": "Intern at ABC",
           "reason_for_shift": "Better growth", "wants_human": False, "needs_other_way": False, "summary": "Short talk."}


def check(name, ok, info=""):
    results.append(("PASS" if ok else "FAIL", name, str(info)[:100]))


def status(cid):
    return get_one("SELECT current_status FROM candidates WHERE id = :id", {"id": cid}).current_status


def token_of(cid):
    return get_one("SELECT access_token FROM candidates WHERE id = :id", {"id": cid}).access_token


def new_candidate(cid):
    run_sql("INSERT INTO candidates (id, job_id, name, email, phone, current_status) VALUES (:id, 1, :n, :e, '', 'Scored (HR Review)')",
            {"id": cid, "n": f"Person {cid}", "e": f"p{cid}@example.com"})
    approve_for_calling(cid, "hr")


def page_text(page):
    """Every text the page shows (st.html, markdown, alerts), as one string."""
    return " ".join(str(getattr(e, "value", "") or getattr(e, "body", "")) for e in page.main)


def candidate_page(token):
    page = AppTest.from_file(str(ROOT / "frontend" / "app.py"), default_timeout=60)
    if token is not None:
        page.query_params["token"] = token
    page.run()
    return page


run_sql("INSERT INTO jobs (title, job_description, level, work_type, scoring_weights) VALUES ('Junior Python Developer','x','Junior','Remote','f')")

# ---------- 1. Send the link ----------
check("1 APP_URL set → browser talks on", web_calls_on())
new_candidate(1)
sent = send_call_link(1, "hr")
token = token_of(1)
check("1 link sent (MOCK email) → Screening Pending", sent == "MOCK" and status(1) == "Screening Pending", sent)
check("1 a long secret token is saved", token and len(token) >= 30, token)
check("1 the email is logged", get_one("SELECT COUNT(*) AS n FROM communication_logs WHERE candidate_id = 1 AND template_name = 'Call link'").n == 1)
send_call_link(1, "hr")
check("1 sent again → the same link", token_of(1) == token)
check("1 link looks right", web_call.make_link(1) == f"https://nexora-test.streamlit.app/?token={token}")

# ---------- 2. Find the candidate from the link ----------
found = candidate_by_token(token)
check("2 right token → the candidate", found and found["id"] == 1 and found["job_title"] == "Junior Python Developer", found)
check("2 wrong token → nobody", candidate_by_token("wrong-token") is None)
check("2 no token → nobody", candidate_by_token(None) is None and candidate_by_token("") is None)

# ---------- 3. The candidate's page ----------
page = candidate_page(token)
text = page_text(page)
check("3 page opens with no error", not page.exception, page.exception)
check("3 says hello to the candidate", "Hello Person 1" in text and "Junior Python Developer" in text, text[:100])
check("3 no HR page: no login form, no Blind Mode", "Log in" not in text and not page.sidebar.toggle, text[:100])
check("3 has the I have finished button", any(b.label == "I have finished" for b in page.button))
page = candidate_page("wrong-token")
check("3 wrong link → 'This link doesn't work'", "This link doesn" in page_text(page) and not page.exception)

# ---------- 4. Save the talk (ElevenLabs pretended) ----------
web_call.find_web_call = lambda cid: None
check("4 no talk on ElevenLabs yet → 'No talk yet'", save_web_call(1, "candidate") == "No talk yet")
web_call.find_web_call = lambda cid: f"conv-{cid}"
web_call.get_call_result = lambda conversation_id: None
check("4 talk still being processed → 'Not finished'", save_web_call(1, "candidate") == "Not finished")
web_call.get_call_result = lambda conversation_id: dict(ANSWERS)
check("4 talk done → 'Saved'", save_web_call(1, "candidate") == "Saved" and status(1) == "Screening Completed (HR Review)")
row = get_one("SELECT conversation_id, candidate_availability, summary FROM screenings WHERE candidate_id = 1")
check("4 answers saved with the talk's id", row.conversation_id == "conv-1" and row.candidate_availability == "Monday 3 pm", row)
check("4 clicked twice → saved once", save_web_call(1, "candidate") == "Already saved"
      and get_one("SELECT COUNT(*) AS n FROM screenings WHERE candidate_id = 1").n == 1)

# ---------- 5. The link after the answers are saved ----------
page = candidate_page(token)
check("5 same link later → 'Thank you', no agent", "Thank you, Person 1" in page_text(page)
      and not any(b.label == "I have finished" for b in page.button))

# ---------- 6. The I have finished button ----------
new_candidate(2)
send_call_link(2, "hr")
page = candidate_page(token_of(2))
[b for b in page.button if b.label == "I have finished"][0].click().run()
check("6 'I have finished' saves the answers", not page.exception and status(2) == "Screening Completed (HR Review)", page.exception)

# ---------- 7. HR's profile: Send the link, then Get the answers ----------
new_candidate(3)
hr = AppTest.from_file(str(ROOT / "frontend" / "pages" / "candidates" / "candidates.py"), default_timeout=60)
hr.session_state.user = {"name": "HR", "email": "hr@test", "role": "HR"}
hr.session_state.blind = False
hr.session_state.picked_candidate = 3
hr.run()
[b for b in hr.button if b.label.startswith("Send the link to")][0].click().run()
check("7 HR: Send the link → Screening Pending", not hr.exception and status(3) == "Screening Pending", hr.exception)
check("7 HR: now shows Get the answers", any(b.label == "Get the answers" for b in hr.button))
[b for b in hr.button if b.label == "Get the answers"][0].click().run()
check("7 HR: Get the answers saves them", status(3) == "Screening Completed (HR Review)")

# ---------- 8. The real ElevenLabs list (read only, no minutes used) ----------
import importlib
importlib.reload(web_call)                                    # the real find_web_call again
try:
    check("8 real ElevenLabs: unknown candidate → None", web_call.find_web_call(999999, look_at=5) is None)
except Exception as error:
    check("8 real ElevenLabs: unknown candidate → None", False, error)

for result, name, info in results:
    print(f"{result}  {name}  ->  {info}")
print(f"{sum(r == 'PASS' for r, _, _ in results)} PASS, {sum(r == 'FAIL' for r, _, _ in results)} FAIL")
