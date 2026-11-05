# Jobs: save a new job with its skills, and read jobs back for the Jobs page.
# No call questions here: the script agent asks the same questions for every job (app/agents/script_agent/prompts.py)
from sqlalchemy import text

from app.core.audit import add_audit_event
from app.core.database.database import engine

LEVELS = ["Junior", "Mid", "Senior", "Team Lead"]
WORK_TYPES = ["Office", "Remote", "Hybrid"]
SKILL_TYPES = ["Must-have", "Nice-to-have"]


# Checks the New job form. Gives back an error message, or None when it is fine
def check_new_job(title, description, level, work_type, skills):
    if not title.strip():
        return "Please write the job title."
    if not description.strip():
        return "Please write the job post."
    if level not in LEVELS:
        return f"Level must be one of: {', '.join(LEVELS)}"
    if work_type not in WORK_TYPES:
        return f"Work type must be one of: {', '.join(WORK_TYPES)}"
    if not skills:
        return "Add at least one skill."
    for skill in skills:
        if skill["type"] not in SKILL_TYPES:
            return f"Pick Must-have or Nice-to-have for {skill['name']}."
        if not 1 <= skill["required_level"] <= 5:
            return f"The required level for {skill['name']} must be 1 to 5."
    return None


# Saves the job and its skills together.
# engine.begin() is one transaction: if any INSERT fails, nothing is saved
def save_job(title, description, level, min_experience, location, work_type, hiring_manager_id,
             skills, saved_by):
    with engine.begin() as conn:
        result = conn.execute(
            text("""
                INSERT INTO jobs (title, job_description, level, min_experience, location, work_type,
                                  hiring_manager_id, scoring_weights)
                VALUES (:title, :description, :level, :min_experience, :location, :work_type,
                        :hiring_manager_id, :scoring_weights)
            """),
            {
                "title": title.strip(),
                "description": description.strip(),
                "level": level,
                "min_experience": min_experience,
                "location": location.strip(),
                "work_type": work_type,
                "hiring_manager_id": hiring_manager_id,
                # The weights are fixed per level and live in prompts.py, so I only note that here
                "scoring_weights": f"Fixed for {level} in prompts.py",
            },
        )
        # lastrowid = the id SQLite just gave the new job
        job_id = result.lastrowid

        for skill in skills:
            conn.execute(
                text("""
                    INSERT INTO job_skills (job_id, name, skill_type, required_level, min_years)
                    VALUES (:job_id, :name, :skill_type, :required_level, :min_years)
                """),
                {
                    "job_id": job_id,
                    "name": skill["name"],
                    "skill_type": skill["type"],
                    "required_level": skill["required_level"],
                    "min_years": skill["min_years"],
                },
            )

    add_audit_event(saved_by, "job created", "job", job_id, f"title: {title.strip()}")
    return job_id


# Reads every job, newest first, with its skills and number of candidates
def list_jobs() -> list[dict]:
    with engine.begin() as conn:
        jobs = conn.execute(text("""
            SELECT jobs.id, jobs.title, jobs.job_description, jobs.level, jobs.min_experience,
                   jobs.location, jobs.work_type, jobs.status, jobs.created_at,
                   employees.name AS manager_name,
                   (SELECT COUNT(*) FROM candidates WHERE candidates.job_id = jobs.id) AS candidate_count
            FROM jobs
            LEFT JOIN employees ON employees.id = jobs.hiring_manager_id
            ORDER BY jobs.id DESC
        """)).mappings().all()

        job_list = []
        for job in jobs:
            skills = conn.execute(
                text("""
                    SELECT name, skill_type, required_level, min_years
                    FROM job_skills
                    WHERE job_id = :job_id
                    ORDER BY id
                """),
                {"job_id": job["id"]},
            ).mappings().all()
            job_list.append({**job, "skills": [dict(skill) for skill in skills]})
    return job_list


# Active employees, so HR can pick a hiring manager. Empty until the Employees page is connected
def list_employee_names():
    with engine.begin() as conn:
        return conn.execute(text("""
            SELECT id, name
            FROM employees
            WHERE is_active = 1
            ORDER BY name
        """)).mappings().all()
