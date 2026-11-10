from app.core.database.database import run_sql
from app.agents.resume_scoring.agent import score_cv
from app.agents.resume_scoring.safety import find_trick_lines
from app.agents.resume_scoring.save_score import save_score
from app.agents.resume_scoring.reader import read_resume

# A fake job and candidate. OR IGNORE skips them if they're already there
run_sql("INSERT OR IGNORE INTO jobs (id, title, job_description, level, scoring_weights) VALUES (1, 'Junior Python Developer', 'Test job', 'Junior', 'in the prompt')")
run_sql("INSERT OR IGNORE INTO candidates (id, job_id, name, email) VALUES (1, 1, 'Test Candidate', 'test@example.test')")

# Score the CV
resume_text = read_resume("sample_data/resumes/11_imran_qureshi_hidden_trick_line.pdf")
result = score_cv("Junior", "Junior Python Developer", "Python, SQL, Git", resume_text)

# Save the result for candidate 1 and job 1
save_score(1, 1, result, find_trick_lines(resume_text))
print("Saved score:", result.total_score)
