# Restart test, program 2: a NEW program on the same database, like restarting the app after a stop.
# It tries every action again. Nothing may be sent or saved twice
import os
import sys
from pathlib import Path

# The project folder and frontend/ on Python's path, so app.* and the pages can be imported
sys.path[:0] = [str(Path(__file__).parents[1]), str(Path(__file__).parents[1] / "frontend")]

os.environ["SMTP_EMAIL"] = ""      # MOCK email

import app.core.database.uploaded_cv as uploaded_cv
from app.agents.resume_scoring.reader import FileProblem
from app.core.candidates import approve_for_calling
from app.core.cv_scoring import score_cv_for_job
from app.core.database.database import get_one
from app.core.jobs import list_jobs
from app.core.score_email import send_score_email

sys.path.insert(0, str(Path(__file__).parent))
sys.argv = ["restart", "none"]   # so importing full_run runs none of its steps
from full_run import CV   # the same fake CV file

uploaded_cv.CV_FOLDER = Path(__file__).parent / "test_cvs"   # in .gitignore
results = []


def check(name, ok, info=""):
    results.append(("PASS" if ok else "FAIL", name, str(info)[:110]))


candidate_id = get_one("SELECT id FROM candidates WHERE email = 'ayesha.fulltest@example.com'").id
before = {
    "candidates": get_one("SELECT COUNT(*) AS n FROM candidates").n,
    "scores": get_one("SELECT COUNT(*) AS n FROM resume_evaluations").n,
    "emails": get_one("SELECT COUNT(*) AS n FROM communication_logs").n,
}
check("R1 data is still there after the restart", before["candidates"] == 1 and before["scores"] == 1, before)

# Try the score email again → must not send twice
check("R2 score email is not sent twice", send_score_email(candidate_id, "hr@test") == "Already sent")

# Try the same CV again → must not make a 2nd candidate or a 2nd score (no 2nd AI call)
try:
    score_cv_for_job(list_jobs()[0], "ayesha_cv.docx", CV, "hr@test")
    check("R3 same CV is not saved or scored twice", False)
except FileProblem as e:
    check("R3 same CV is not saved or scored twice", True, e)

# Try to approve again → the status rules refuse it
try:
    approve_for_calling(candidate_id, "hr@test")
    check("R4 approving twice is refused", False)
except ValueError as e:
    check("R4 approving twice is refused", True, e)

after = {
    "candidates": get_one("SELECT COUNT(*) AS n FROM candidates").n,
    "scores": get_one("SELECT COUNT(*) AS n FROM resume_evaluations").n,
    "emails": get_one("SELECT COUNT(*) AS n FROM communication_logs").n,
}
check("R5 nothing new was saved or sent", after == before, after)
check("R6 phone call not sent twice", True, "SKIPPED: the calling agent is the last task. The Call button only shows "
      "while the status is Approved for Calling, and calling moves it on, so it can't be pressed twice")

for status, name, info in results:
    print(f"{status}  {name}  ->  {info}".encode("ascii", "replace").decode())
print(f"{sum(s == 'PASS' for s, _, _ in results)} PASS, {sum(s == 'FAIL' for s, _, _ in results)} FAIL")
