# Agent 3's steps, top to bottom. Nothing is sent here: HR says yes first, on the Interviews page
#   read the candidate's times (AI) → find times for both (rules) → write the invite (AI) → save the proposal
#   no time works → an HR to-do instead
from app.agents.scheduling.agent import read_availability, write_invite
from app.agents.scheduling.free_times import find_free_slots
from app.agents.scheduling.save_interview import save_proposal
from app.core.database.database import get_one
from app.core.hr_tasks import add_task
from app.core.settings import get_settings


# Gives back "Proposed" or "No free slot"
def plan_interview(candidate_id, hr_email):
    settings = get_settings()
    person = get_one("""
        SELECT candidates.name, jobs.title,
               (SELECT candidate_availability FROM screenings WHERE candidate_id = candidates.id ORDER BY id DESC) AS said
        FROM candidates JOIN jobs ON jobs.id = candidates.job_id
        WHERE candidates.id = :id
    """, {"id": candidate_id})
    if person is None:
        raise ValueError(f"Candidate {candidate_id} not found")

    said = (person.said or "").strip()
    windows = read_availability(said, settings) if said else []
    # The candidate gave times, but none can be used (too far away, or unclear) → HR decides, never "any time"
    slots = [] if said and not windows else find_free_slots(windows, settings)

    if not slots:
        add_task("No interview time works for both sides", "No free slot", candidate_id,
                 "Check the interviewers' free times, or ask the candidate for more times.", hr_email)
        return "No free slot"

    save_proposal(candidate_id, slots, write_invite(person.name, person.title, slots[0], settings), settings, hr_email)
    return "Proposed"
