from app.core.database.database import run_sql, get_one
from app.agents.resume_scoring.agent import score_cv
from app.agents.resume_scoring.safety import find_trick_lines
from app.agents.resume_scoring.save_score import save_score
from app.parsing.reader import read_resume

# A fake job and a fake candidate, so the score has something to link to
run_sql("""
    INSERT INTO jobs (title, job_description, level, scoring_weights)
    VALUES ('Junior Python Developer', 'Fake job for testing', 'Junior', 'in the prompt')
""")
job_id = get_one("SELECT max(id) AS id FROM jobs").id

run_sql("""
    INSERT INTO candidates (job_id, name, email)
    VALUES (:job_id, 'Test Candidate', 'test@example.test')
""", {"job_id": job_id})
candidate_id = get_one("SELECT max(id) AS id FROM candidates").id

# Score the CV, then save the result
resume_text = read_resume("sample_data/resumes/11_imran_qureshi_hidden_trick_line.pdf")
result = score_cv("Junior", "Junior Python Developer", "Python, SQL, Git", resume_text)
save_score(candidate_id, job_id, result, find_trick_lines(resume_text))

row = get_one(
    "SELECT total_score, missing_skills, warnings FROM resume_evaluations WHERE candidate_id = :id",
    {"id": candidate_id},
)
print("Saved:", row.total_score, row.missing_skills, row.warnings)
