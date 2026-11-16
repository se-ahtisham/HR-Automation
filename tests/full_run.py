# Day 8 full test run: job → CV → score → approve → score email → (pretend) call → approve for interview →
# Agent 3 finds a time → HR sends the invite → to-do → dashboard → history → fix → delete. (Schedule steps added on Day 7.)
# Uses the TEST database (DATABASE_URL), a fake CV, and MOCK email (no real email is sent).
# Run it (PowerShell), never on my real database:
#   $env:DATABASE_URL = "sqlite:///./tests/test.db"; uv run python -m app.core.database.init_db
#   uv run python tests/full_run.py all
# Restart test: delete tests/test.db, init_db again, then:  full_run.py first  →  restart_run.py
import io
import json
import os
import sys
import zipfile
from pathlib import Path

# The project folder and frontend/ on Python's path, so app.* and the pages can be imported
sys.path[:0] = [str(Path(__file__).parents[1]), str(Path(__file__).parents[1] / "frontend")]

os.environ["SMTP_EMAIL"] = ""            # MOCK email: set BEFORE importing score_email
os.environ["APP_URL"] = ""   # no browser link: these tests use the pretend call (web_call_test.py tests the link)
STEP = sys.argv[1] if len(sys.argv) > 1 else "all"

from streamlit.testing.v1 import AppTest

import app.core.database.uploaded_cv as uploaded_cv
from app.agents.resume_scoring.reader import FileProblem
from app.core.audit import list_history
from app.agents.scheduling.flow import plan_interview
from app.agents.scheduling.save_interview import list_interviews, send_invite
from app.agents.script_agent.save_call import save_call_result, save_call_started
from app.core.candidates import (approve_for_calling, approve_for_interview, delete_old_candidates, fix_candidate,
                                 list_candidates)
from app.core.cv_scoring import score_cv_for_job
from app.core.database.database import get_one, run_sql
from app.core.employees import save_employee
from app.core.hr_tasks import add_task, list_tasks
from app.core.jobs import list_jobs, save_job
from app.core.score_email import send_score_email

# CV files from this test go to the scratchpad, never to the project's data/cvs folder
uploaded_cv.CV_FOLDER = Path(__file__).parent / "test_cvs"   # in .gitignore
HR = "hr@test"
results = []


def check(name, ok, info=""):
    results.append(("PASS" if ok else "FAIL", name, str(info)[:100]))


# A real .docx file (a Word file is a zip of XML files), with a fake CV inside
def make_docx(lines):
    body = "".join(f"<w:p><w:r><w:t>{line}</w:t></w:r></w:p>" for line in lines)
    files = {
        "[Content_Types].xml": '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                               '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                               '<Default Extension="xml" ContentType="application/xml"/>'
                               '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>',
        "_rels/.rels": '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                       '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>',
        "word/document.xml": '<?xml version="1.0" encoding="UTF-8"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                             f"<w:body>{body}</w:body></w:document>",
    }
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as z:
        for name, content in files.items():
            z.writestr(name, content)
    return buffer.getvalue()


CV = make_docx([
    "Ayesha Khan", "ayesha.fulltest@example.com | +92 300 1234567 | Lahore",
    "Experience: Python developer at TestSoft, 2 years. Built REST APIs with FastAPI and wrote SQL reports.",
    "Projects: A to-do API with FastAPI and SQLite. A chat bot with LangChain.",
    "Education: BS Computer Science, 2023.", "Skills: Python, SQL, FastAPI, Git, Docker.",
])

if STEP in ("all", "first"):
    # 1. Employees and a job
    sara = save_employee(None, "Sara Interviewer", "sara.int@example.com", "Interviewer", "Backend", "Asia/Karachi", True,
                         [{"day_of_week": day, "start_time": "10:00", "end_time": "13:00"}
                          for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]], HR)
    save_job("Junior Python Developer", "We need a junior Python developer for APIs with FastAPI and SQL.", "Junior", 0, "Lahore",
             "Hybrid", sara, [{"name": "Python", "type": "Must-have", "required_level": 3, "min_years": None},
                              {"name": "SQL", "type": "Must-have", "required_level": 2, "min_years": None}], HR)
    job = list_jobs()[0]
    check("1 job saved with skills and hiring manager", len(job["skills"]) == 2 and job["manager_name"] == "Sara Interviewer", job["title"])

    # 2. Upload + score a real .docx CV (real AI)
    candidate_id, result = score_cv_for_job(job, "ayesha_cv.docx", CV, HR)
    person = get_one("SELECT name, email, phone, current_status FROM candidates WHERE id = :id", {"id": candidate_id})
    check("2 CV read: name, email, phone", person.email == "ayesha.fulltest@example.com" and person.phone.startswith("+92"), tuple(person))
    check("2 CV scored, status Scored (HR Review)", result is not None and person.current_status == "Scored (HR Review)",
          f"score {result and result['total_score']}")

    # 3. The same CV again is blocked (one person, one application)
    try:
        score_cv_for_job(job, "ayesha_cv.docx", CV, HR)
        check("3 same CV again is blocked", False)
    except FileProblem as e:
        check("3 same CV again is blocked", True, e)

    # 4. HR stop #1 and the score email
    approve_for_calling(candidate_id, HR)
    check("4 approved for calling", get_one("SELECT current_status FROM candidates WHERE id = :id", {"id": candidate_id}).current_status == "Approved for Calling")
    check("5 score email (MOCK)", send_score_email(candidate_id, HR) == "MOCK")

    # 6. The talk: a PRETEND result here (the real browser talk is tested in tests/web_call_test.py)
    save_call_started(candidate_id, "pretend-call-1", HR)
    save_call_result(candidate_id, "pretend-call-1", {"consent_given": True, "available_date_time": "any working day, any time",
                                                     "previous_job": "Intern at TestSoft", "reason_for_shift": "To grow",
                                                     "summary": "Pretend call for the test."}, HR)
    check("6 pretend call saved, status Screening Completed (HR Review)",
          get_one("SELECT current_status FROM candidates WHERE id = :id", {"id": candidate_id}).current_status == "Screening Completed (HR Review)")

    # 6b. HR stop #2 → Agent 3 finds a time → HR stop #3: HR sends the invite (MOCK)
    approve_for_interview(candidate_id, HR)
    check("6b Agent 3 proposes times", plan_interview(candidate_id, HR) == "Proposed")
    interview = list_interviews()[0]
    slots = json.loads(interview["proposed_slots"])
    draft = json.loads(interview["email_draft"])
    check("6b times are with Sara, inside her free time", all(s["interviewer"] == "Sara Interviewer" and "10:00" <= s["start"][11:] < "13:00" for s in slots),
          [s["start"] for s in slots])
    check("6b invite written", bool(draft["body"].strip()), draft["subject"])
    check("6b invite sent once (MOCK)", send_invite(interview["id"], slots[0], draft["subject"], draft["body"], HR) == "MOCK"
          and get_one("SELECT current_status FROM candidates WHERE id = :id", {"id": candidate_id}).current_status == "Interview Scheduled")

    # 7. A to-do
    add_task("Call Ayesha back about her interview time", "Human requested", candidate_id, "Test note", HR)
    check("7 to-do added", len(list_tasks("Open")) == 1)

if STEP in ("all", "second"):
    candidate_id = get_one("SELECT id FROM candidates WHERE email = 'ayesha.fulltest@example.com'").id

    # 8. Dashboard shows the real data
    at = AppTest.from_file(str(Path(__file__).parents[1] / "frontend" / "app.py"), default_timeout=60)
    at.session_state.user = {"name": "HR Test", "email": HR, "role": "HR"}
    at.run()
    page_text = " ".join(str(h.proto) for h in at.get("html"))
    check("8 dashboard loads", not at.exception, at.exception)
    check("8 dashboard shows the candidate and activity", "Ayesha Khan" in page_text and "Interview invite" in page_text)
    check("8 dashboard shows the open to-do", any(c.label.startswith("Call Ayesha") for c in at.checkbox))

    # 9. History on the profile
    actions = [event["action"] for event in list_history("candidate", candidate_id)]
    check("9 history has every step", {"CV uploaded", "CV scored", "Approved for calling", "CV Match Score email", "Call result saved",
                                       "Approved for interview", "Interview times proposed", "Interview invite"} <= set(actions), actions)
    at2 = AppTest.from_file(str(Path(__file__).parents[1] / "frontend" / "pages" / "candidates" / "candidates.py"), default_timeout=60)
    at2.session_state.user = {"name": "HR Test", "email": HR, "role": "HR"}
    at2.session_state.picked_candidate = candidate_id
    at2.run()
    check("9 profile shows History and Fix details", not at2.exception and "History" in [e.label for e in at2.expander], at2.exception)

    # 10. Fix details
    check("10 fix: bad email refused", fix_candidate(candidate_id, "Ayesha Khan", "nope", "+923001234567", HR) is not None)
    check("10 fix: saved", fix_candidate(candidate_id, "Ayesha K. Khan", "ayesha.fulltest@example.com", "+923001234567", HR) is None
          and get_one("SELECT name FROM candidates WHERE id = :id", {"id": candidate_id}).name == "Ayesha K. Khan")

    # 11. Auto clean-up of old data
    run_sql("INSERT INTO candidates (job_id, name, email, created_at) VALUES (1, 'Old Person', 'old@example.com', '2020-01-01 10:00:00')")
    deleted = delete_old_candidates()
    check("11 clean-up deletes only old data", deleted == 1 and get_one("SELECT COUNT(*) AS n FROM candidates").n == 1, f"deleted {deleted}")

for status, name, info in results:
    print(f"{status}  {name}  ->  {info}".encode("ascii", "replace").decode())
print(f"{sum(s == 'PASS' for s, _, _ in results)} PASS, {sum(s == 'FAIL' for s, _, _ in results)} FAIL")
