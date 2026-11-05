from app.core.database.database import get_one, run_sql

# Each status lists the only next steps allowed
ALLOWED_MOVES = {
    "Resume Received": ["Scored (HR Review)", "Needs Manual Review", "Closed"],
    "Needs Manual Review": ["Resume Received", "Closed"],
    "Scored (HR Review)": ["Approved for Calling", "Closed"],
    "Approved for Calling": ["Screening Pending", "Closed"],
    "Screening Pending": ["Screening Completed (HR Review)", "Needs Manual Review", "Closed"],
    "Screening Completed (HR Review)": ["Approved for Interview", "Closed"],
    "Approved for Interview": ["Interview Proposed", "Closed"],
    "Interview Proposed": ["Interview Scheduled", "Needs Manual Review", "Closed"],
    "Interview Scheduled": ["Interview Proposed", "Closed"],
    "Closed": [],
}

def change_status(candidate_id, new_status):
    row = get_one(
        "SELECT current_status FROM candidates WHERE id = :id",
        {"id": candidate_id},
    )

    if row is None:
        raise ValueError(f"Candidate {candidate_id} not found")

    if new_status not in ALLOWED_MOVES[row.current_status]:
        raise ValueError(f"Can't move from {row.current_status} to {new_status}")

    run_sql(
        "UPDATE candidates SET current_status = :status WHERE id = :id",
        {"status": new_status, "id": candidate_id},
    )
