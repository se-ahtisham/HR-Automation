-- Stores each candidate, their CV text and their current status
CREATE TABLE IF NOT EXISTS candidates (
    id INTEGER PRIMARY KEY,
    job_id INTEGER REFERENCES jobs (id),
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT, -- Read from the CV. The call agent calls this number
    resume_path TEXT,
    resume_text TEXT,
    current_status TEXT NOT NULL DEFAULT 'Resume Received',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_candidates_status
ON candidates (current_status);

-- Stores the HR accounts that log in to the app.
-- Not the same as employees: employees are the staff HR adds and schedules for interviews
CREATE TABLE IF NOT EXISTS hr_accounts (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL, -- Scrambled by bcrypt. Never the real password
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Stores company staff that HR adds: their roles, time zone and whether they can interview.
-- They don't log in. HR sets their free times for scheduling
CREATE TABLE IF NOT EXISTS employees (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    role TEXT NOT NULL,
    team TEXT,
    timezone TEXT NOT NULL DEFAULT 'Asia/Karachi',
    can_interview INTEGER NOT NULL DEFAULT 0, -- Default false, because a new employee does not interview yet
    is_active INTEGER NOT NULL DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_employees_can_interview
ON employees (can_interview);

-- Stores the weekly days and times each interviewer is free
CREATE TABLE IF NOT EXISTS employee_availability (
    id INTEGER PRIMARY KEY,
    employee_id INTEGER NOT NULL REFERENCES employees (id),
    day_of_week TEXT NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_availability_employee_day
ON employee_availability (employee_id, day_of_week);

-- Stores one-off busy times like leave and meetings
CREATE TABLE IF NOT EXISTS employee_busy_times (
    id INTEGER PRIMARY KEY,
    employee_id INTEGER NOT NULL REFERENCES employees (id),
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    reason TEXT
);

CREATE INDEX IF NOT EXISTS idx_busy_times_employee
ON employee_busy_times (employee_id);

-- Stores each job post with its level, location and scoring weights
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    job_description TEXT NOT NULL,
    level TEXT NOT NULL CHECK (level IN ('Junior', 'Mid', 'Senior', 'Team Lead')),
    min_experience INTEGER,
    location TEXT,
    work_type TEXT CHECK (work_type IN ('Office', 'Remote', 'Hybrid')),
    hiring_manager_id INTEGER REFERENCES employees (id),
    scoring_weights TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Open',
    created_by INTEGER REFERENCES employees (id),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_jobs_status
ON jobs (status);

-- Stores the skills for each job and the required level of each skill
CREATE TABLE IF NOT EXISTS job_skills (
    id INTEGER PRIMARY KEY,
    job_id INTEGER NOT NULL REFERENCES jobs (id),
    name TEXT NOT NULL,
    skill_type TEXT NOT NULL CHECK (skill_type IN ('Must-have', 'Nice-to-have')),
    importance INTEGER NOT NULL DEFAULT 1,
    required_level INTEGER NOT NULL DEFAULT 1 CHECK (required_level BETWEEN 1 AND 5),
    min_years INTEGER
);

CREATE INDEX IF NOT EXISTS idx_job_skills_job
ON job_skills (job_id);

-- Stores the call questions for each job in the right order
CREATE TABLE IF NOT EXISTS screening_questions (
    id INTEGER PRIMARY KEY,
    job_id INTEGER NOT NULL REFERENCES jobs (id),
    question TEXT NOT NULL,
    question_order INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_screening_questions_job
ON screening_questions (job_id);

-- Stores the starting scoring weights for each job level
CREATE TABLE IF NOT EXISTS level_weights (
    level TEXT PRIMARY KEY CHECK (level IN ('Junior', 'Mid', 'Senior', 'Team Lead')),
    weights TEXT NOT NULL
);

-- Stores the score, proof and missing skills from Agent 1
CREATE TABLE IF NOT EXISTS resume_evaluations (
    id INTEGER PRIMARY KEY,
    candidate_id INTEGER NOT NULL REFERENCES candidates (id),
    job_id INTEGER NOT NULL REFERENCES jobs (id),
    total_score INTEGER CHECK (total_score BETWEEN 0 AND 100),
    criterion_scores TEXT,
    skill_scores TEXT,
    strengths TEXT,
    weak_points TEXT,
    missing_skills TEXT,
    proof_lines TEXT,
    warnings TEXT,
    model_version TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_evaluations_candidate
ON resume_evaluations (candidate_id);

-- Stores the one set of scheduling rules that HR can change
CREATE TABLE IF NOT EXISTS scheduling_settings (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    interview_minutes INTEGER NOT NULL DEFAULT 45,
    break_minutes INTEGER NOT NULL DEFAULT 15,
    timezone TEXT NOT NULL DEFAULT 'Asia/Karachi',
    booking_days INTEGER NOT NULL DEFAULT 7,
    notice_hours INTEGER NOT NULL DEFAULT 24,
    time_choices INTEGER NOT NULL DEFAULT 3,
    max_per_day INTEGER NOT NULL DEFAULT 4,
    meeting_type TEXT NOT NULL DEFAULT 'Online',
    call_tries INTEGER NOT NULL DEFAULT 2,
    keep_data_days INTEGER NOT NULL DEFAULT 90,
    auto_score_email INTEGER NOT NULL DEFAULT 1,
    updated_by INTEGER REFERENCES employees (id),
    updated_at TEXT
);

-- Stores each screening call, its consent, answers and summary
CREATE TABLE IF NOT EXISTS screenings (
    id INTEGER PRIMARY KEY,
    candidate_id INTEGER NOT NULL REFERENCES candidates (id),
    call_status TEXT NOT NULL DEFAULT 'Pending',
    consent_status TEXT NOT NULL DEFAULT 'Not asked',
    answers TEXT,
    candidate_availability TEXT,
    unresolved_questions TEXT,
    summary TEXT,
    next_step TEXT,
    call_tries INTEGER NOT NULL DEFAULT 0,
    conversation_id TEXT, -- The call's id on ElevenLabs, to get the answers back
    reviewed_by INTEGER REFERENCES employees (id),
    reviewed_at TEXT,
    call_time TEXT
);

CREATE INDEX IF NOT EXISTS idx_screenings_candidate
ON screenings (candidate_id);

-- Stores interview times, the email draft and HR approval
CREATE TABLE IF NOT EXISTS interviews (
    id INTEGER PRIMARY KEY,
    candidate_id INTEGER NOT NULL REFERENCES candidates (id),
    interviewer_id INTEGER REFERENCES employees (id),
    proposed_slots TEXT,
    confirmed_slot TEXT,
    timezone TEXT,
    meeting_details TEXT,
    email_draft TEXT,
    approval_status TEXT NOT NULL DEFAULT 'Pending',
    send_status TEXT NOT NULL DEFAULT 'Not sent',
    status TEXT NOT NULL DEFAULT 'Proposed',
    sent_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_interviews_candidate
ON interviews (candidate_id);

-- Stores email text and call scripts with version numbers
CREATE TABLE IF NOT EXISTS email_templates (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    subject TEXT,
    body TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (name, version)
);

-- Stores a record of every email and call sent to a candidate
CREATE TABLE IF NOT EXISTS communication_logs (
    id INTEGER PRIMARY KEY,
    candidate_id INTEGER NOT NULL REFERENCES candidates (id),
    channel TEXT NOT NULL,
    template_name TEXT,
    template_version INTEGER,
    delivery_status TEXT NOT NULL DEFAULT 'Pending',
    provider_reference TEXT,
    sent_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_communication_candidate
ON communication_logs (candidate_id);

-- Stores the HR to-do list for problems the app cannot solve alone
CREATE TABLE IF NOT EXISTS hr_tasks (
    id INTEGER PRIMARY KEY,
    candidate_id INTEGER REFERENCES candidates (id),
    title TEXT NOT NULL,
    task_type TEXT NOT NULL DEFAULT 'Other', -- Like "No free slot" or "Human requested"
    note TEXT, -- HR's own notes about the task
    status TEXT NOT NULL DEFAULT 'Open',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    done_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_hr_tasks_status
ON hr_tasks (status);

-- Stores the history of who did what and when
CREATE TABLE IF NOT EXISTS audit_events (
    id INTEGER PRIMARY KEY,
    actor TEXT NOT NULL,
    action TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id INTEGER NOT NULL,
    timestamp TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    details TEXT
);

CREATE INDEX IF NOT EXISTS idx_audit_entity
ON audit_events (entity_type, entity_id);
