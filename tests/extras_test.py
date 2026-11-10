# Day 9 "Test the extras": Blind Review Mode, the AI Job Post Writer, and the CV Match Score email.
# Uses the TEST database and MOCK email (nothing is really sent). Run it (PowerShell), never on my real database:
#   $env:DATABASE_URL = "sqlite:///./tests/test.db"; uv run python -m app.core.database.init_db
#   uv run python tests/extras_test.py
import json
import os
import sys
from pathlib import Path

sys.path[:0] = [str(Path(__file__).parents[1]), str(Path(__file__).parents[1] / "frontend")]
os.environ["SMTP_EMAIL"] = ""          # MOCK email: set BEFORE importing score_email
sys.stdout.reconfigure(encoding="utf-8")

from app.agents.job_writer.agent import write_job_post
from app.core.blind import clean_cv
from app.core.database.database import run_sql
from app.core.score_email import send_score_email, write_score_email

results = []


def check(name, ok, info=""):
    results.append(("PASS" if ok else "FAIL", name, str(info)[:100]))


# ---------- 1. Blind Review Mode ----------
cv_a = "Ahmed Khan\nahmed.khan@example.com | +92 300 1111111 | linkedin.com/in/ahmed\nPython developer (2019 - 2023) at TestSoft."
cv_b = "Ayesha Siddiqui\nayesha.s@example.com | +92 321 2222222 | linkedin.com/in/ayesha\nPython developer (2019 - 2023) at TestSoft."
clean_a = clean_cv(cv_a, "Ahmed Khan")
check("1 blind: same CV, different names → the same text for the AI", clean_a == clean_cv(cv_b, "Ayesha Siddiqui"))
check("1 blind: no name, email, phone or link left", not any(x in clean_a for x in ["Ahmed", "@", "1111111", "linkedin"]), clean_a)
check("1 blind: dates stay", "2019 - 2023" in clean_a)

# ---------- 2. AI Job Post Writer (real AI) ----------
draft = write_job_post("need junior Python dev, Lahore, hybrid, FastAPI and SQL")
check("2 writer: gives a draft", draft is not None)
if draft:
    check("2 writer: title, level, work type", bool(draft.title) and draft.level == "Junior" and draft.work_type == "Hybrid",
          f"{draft.title} | {draft.level} | {draft.work_type}")
    check("2 writer: 4 to 8 skills with levels 1-5", 4 <= len(draft.skills) <= 8 and all(1 <= s.required_level <= 5 for s in draft.skills),
          [s.name for s in draft.skills])
    check("2 writer: no call questions (removed 5 Nov)", not hasattr(draft, "questions"))
    post = draft.job_post.lower()
    check("2 writer: no protected traits in the post", not any(w in post for w in [" age ", "gender", "religion", "married", "nationality"]))

# ---------- 3. CV Match Score email (MOCK) ----------
run_sql("INSERT INTO jobs (title, job_description, level, work_type, scoring_weights) VALUES ('Junior Python Developer','x','Junior','Remote','f')")
run_sql("INSERT INTO candidates (id, job_id, name, email, current_status) VALUES (1, 1, '<b>Test</b> Person', 't@example.com', 'Scored (HR Review)')")
run_sql("""INSERT INTO resume_evaluations (candidate_id, job_id, total_score, strengths, weak_points, missing_skills)
           VALUES (1, 1, 74, :good, :weak, '[]')""", {"good": json.dumps(["Strong Python"]), "weak": json.dumps(["Little testing"])})
to, subject, html = write_score_email(1)
check("3 email: to the candidate, with the score", to == "t@example.com" and "74/100" in subject, subject)
check("3 email: strengths and weak points in it", "Strong Python" in html and "Little testing" in html)
check("3 email: an empty list says None", "<li>None</li>" in html)
check("3 email: 'not a hiring decision', never 'rejected'", "not a hiring decision" in html and "reject" not in html.lower())
check("3 email: a strange name is made safe", "&lt;b&gt;Test" in html)
check("3 email: sent once (MOCK)", send_score_email(1, "hr") == "MOCK")
check("3 email: never twice", send_score_email(1, "hr") == "Already sent")

for status, name, info in results:
    print(f"{status}  {name}  ->  {info}")
print(f"{sum(s == 'PASS' for s, _, _ in results)} PASS, {sum(s == 'FAIL' for s, _, _ in results)} FAIL")
