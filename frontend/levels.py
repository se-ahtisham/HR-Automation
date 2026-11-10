# The scoring weights for each job level. They match the tables in app/agents/resume_scoring/prompts.py
# These are real rules, not dummy data: the pages use them to show "Skills 35%" next to each part score.
LEVEL_WEIGHTS = {
    "Junior": {"Skills": 35, "Experience": 10, "Projects": 30, "Education": 20, "Leadership": 0, "Other": 5},
    "Mid": {"Skills": 40, "Experience": 25, "Projects": 20, "Education": 10, "Leadership": 0, "Other": 5},
    "Senior": {"Skills": 35, "Experience": 35, "Projects": 15, "Education": 5, "Leadership": 5, "Other": 5},
    "Team Lead": {"Skills": 25, "Experience": 25, "Projects": 10, "Education": 5, "Leadership": 30, "Other": 5},
}
