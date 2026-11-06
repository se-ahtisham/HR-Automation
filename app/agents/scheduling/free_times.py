# Finds interview times that work for both sides. No AI: exact rules, done with `portion` (a library for time ranges).
#   free time = interviewer's weekly hours − busy times − booked interviews (with a break around each)
#   a good slot = inside the free time AND inside the candidate's times AND inside the Settings rules
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import portion as P
from sqlalchemy import text

from app.core.database.database import engine

# The time now in the company's time zone (all my times are in that one zone)
def now_here(settings):
    return datetime.now(ZoneInfo(settings["timezone"])).replace(tzinfo=None, second=0, microsecond=0)


# Who is free: interviewers who are turned on and can interview, with their times from the database
def find_interviewers():
    with engine.begin() as conn:
        people = conn.execute(text("SELECT id, name FROM employees WHERE can_interview = 1 AND is_active = 1")).mappings().all()
        return [{
            "id": p["id"], "name": p["name"],
            "weekly": conn.execute(text("SELECT day_of_week, start_time, end_time FROM employee_availability WHERE employee_id = :id"),
                                   {"id": p["id"]}).all(),
            "busy": conn.execute(text("SELECT start_time, end_time FROM employee_busy_times WHERE employee_id = :id"),
                                 {"id": p["id"]}).all(),
            "booked": conn.execute(text("SELECT confirmed_slot FROM interviews WHERE interviewer_id = :id "
                                        "AND confirmed_slot IS NOT NULL AND status != 'Cancelled'"), {"id": p["id"]}).scalars().all(),
        } for p in people]


# The times that work for both. candidate_windows = [(start, end), ...]; empty = the candidate gave no time
def find_free_slots(candidate_windows, settings):
    length = timedelta(minutes=settings["interview_minutes"])
    gap = timedelta(minutes=settings["break_minutes"])
    now = now_here(settings)
    days = [now.date() + timedelta(days=n) for n in range(settings["booking_days"] + 1)]

    # When the interview may happen: after the notice time, and inside the candidate's times (if they gave any)
    allowed = P.closedopen(now + timedelta(hours=settings["notice_hours"]), P.inf)
    if candidate_windows:
        allowed &= P.Interval(*[P.closedopen(start, end) for start, end in candidate_windows])

    slots = []
    for person in find_interviewers():
        booked = [datetime.fromisoformat(start) for start in person["booked"]]
        free = P.Interval(*[P.closedopen(datetime.fromisoformat(f"{day} {start}"), datetime.fromisoformat(f"{day} {end}"))
                            for day in days for weekday, start, end in person["weekly"] if weekday == day.strftime("%A")])
        free -= P.Interval(*[P.closedopen(datetime.fromisoformat(str(start)) - gap, datetime.fromisoformat(str(end)) + gap)
                             for start, end in person["busy"]])
        free -= P.Interval(*[P.closedopen(start - gap, start + length + gap) for start in booked])

        # Step through the free time: an interview, a break, the next one...
        for start in P.iterate(free, step=length + gap):
            full_day = sum(b.date() == start.date() for b in booked) >= settings["max_per_day"]
            if P.closedopen(start, start + length) in (free & allowed) and not full_day:
                slots.append({"start": start.isoformat(" ", "minutes"), "end": (start + length).isoformat(" ", "minutes"),
                              "interviewer_id": person["id"], "interviewer": person["name"]})

    # The earliest times first, one interviewer per time, only as many choices as Settings says
    choices = []
    for slot in sorted(slots, key=lambda s: s["start"]):
        if slot["start"] not in [c["start"] for c in choices]:
            choices.append(slot)
    return choices[:settings["time_choices"]]
