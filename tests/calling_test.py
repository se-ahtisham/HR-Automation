# The script agent's saving code, tested with pretend calls: answers saved, problems → HR to-dos, saved only once,
# and the pretend-call form on the profile. (The phone calls, the test-number list and the webhook were removed on 16 Nov:
# no Twilio. The browser talk is tested in web_call_test.py.)
# Test database only:
#   $env:DATABASE_URL = "sqlite:///./tests/test.db"; uv run python -m app.core.database.init_db
#   uv run python tests/calling_test.py
import os
import sys
from pathlib import Path

sys.path[:0] = [str(Path(__file__).parents[1]), str(Path(__file__).parents[1] / "frontend")]
sys.stdout.reconfigure(encoding="utf-8")
os.environ["APP_URL"] = ""   # no browser link: these tests use the pretend call (web_call_test.py tests the link)

from streamlit.testing.v1 import AppTest

from app.agents.script_agent.save_call import save_call_result, save_pretend_call
from app.agents.script_agent.web_call import web_calls_on
from app.core.candidates import approve_for_calling
from app.core.database.database import get_one, run_sql
from app.core.hr_tasks import list_tasks

results = []


def check(name, ok, info=""):
    results.append(("PASS" if ok else "FAIL", name, str(info)[:100]))


def status(cid):
    return get_one("SELECT current_status FROM candidates WHERE id = :id", {"id": cid}).current_status


def new_candidate(cid, phone=""):
    run_sql("INSERT INTO candidates (id, job_id, name, email, phone, current_status) VALUES (:id, 1, :n, :e, :p, 'Scored (HR Review)')",
            {"id": cid, "n": f"Person {cid}", "e": f"p{cid}@example.com", "p": phone})
    approve_for_calling(cid, "hr")


run_sql("INSERT INTO jobs (title, job_description, level, work_type, scoring_weights) VALUES ('Junior Python Developer','x','Junior','Remote','f')")
ANSWERS = {"consent_given": True, "available_date_time": "Tuesday afternoon", "previous_job": "Intern",
           "reason_for_shift": "To grow", "wants_human": False, "needs_other_way": False}

# ---------- 1. Pretend call ----------
check("1 no APP_URL → pretend calls", not web_calls_on())
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
check("2 other language / no phone → to-do", "The candidate needs another language or can't talk now" in titles)

# ---------- 3. Saved only once ----------
conversation = get_one("SELECT conversation_id FROM screenings WHERE candidate_id = 1").conversation_id
check("3 the same result twice → saved once", save_call_result(1, conversation, {**ANSWERS, "summary": "x"}, "hr") == "Already saved")

# ---------- 4. The page shows the pretend-call form ----------
new_candidate(6)
page = AppTest.from_file(str(Path(__file__).parents[1] / "frontend" / "pages" / "candidates" / "candidates.py"), default_timeout=60)
page.session_state.user = {"name": "HR", "email": "hr@test", "role": "HR"}
page.session_state.blind = False
page.session_state.picked_candidate = 6
page.run()
page.text_input(key="mock_when").input("Monday morning")
[b for b in page.button if b.label == "Save pretend call"][0].click().run()
check("4 page: pretend call form works", not page.exception and status(6) == "Screening Completed (HR Review)", page.exception)

for result, name, info in results:
    print(f"{result}  {name}  ->  {info}")
print(f"{sum(r == 'PASS' for r, _, _ in results)} PASS, {sum(r == 'FAIL' for r, _, _ in results)} FAIL")
