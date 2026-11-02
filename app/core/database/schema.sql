CREATE TABLE IF NOT EXISTS candidates (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    resume_path TEXT,
    resume_text TEXT,
    current_status TEXT NOT NULL DEFAULT 'Resume Received',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_candidates_status
ON candidates (current_status);




