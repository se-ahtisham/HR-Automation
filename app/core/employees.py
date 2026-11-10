# Employees: the staff HR adds (interviewers, hiring managers...). They don't log in.
# HR can add, read, change and turn them off (never delete, so old records stay safe). Every change goes into the audit log
from sqlalchemy import text

from app.core.audit import add_audit_event
from app.core.database.database import engine, get_one, run_sql

ROLES = ["Interviewer", "Hiring Manager", "HR", "Admin"]
TIME_ZONES = ["Asia/Karachi", "Asia/Dubai", "Europe/London", "America/New_York"]
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


# Read: every employee, with their weekly free times and busy times
def list_employees():
    with engine.begin() as conn:
        people = conn.execute(text("SELECT * FROM employees ORDER BY is_active DESC, name")).mappings().all()
        employees = []
        for person in people:
            free_times = conn.execute(text("""
                SELECT day_of_week, start_time, end_time FROM employee_availability
                WHERE employee_id = :id ORDER BY id
            """), {"id": person["id"]}).mappings().all()
            busy_times = conn.execute(text("""
                SELECT id, start_time, end_time, reason FROM employee_busy_times
                WHERE employee_id = :id ORDER BY start_time
            """), {"id": person["id"]}).mappings().all()
            employee = dict(person)
            employee["free_times"] = [dict(t) for t in free_times]
            employee["busy_times"] = [dict(b) for b in busy_times]
            employees.append(employee)
    return employees


# Checks the form. Gives back an error message, or None when it is fine
def check_employee(employee_id, name, email, free_times):
    if not name.strip():
        return "Please write the name."
    if "@" not in email or "." not in email:
        return "Please write a real email address."
    # Two employees can't share an email (the column is UNIQUE)
    same = get_one("SELECT id FROM employees WHERE email = :email AND id != :id",
                   {"email": email.strip().lower(), "id": employee_id or 0})
    if same:
        return "Another employee already has this email."
    for time in free_times:
        if time["start_time"] >= time["end_time"]:
            return f"On {time['day_of_week']}, the start time must be before the end time."
    return None


# Create or Update: saves the person and their weekly free times in one transaction.
# employee_id = None makes a new person
def save_employee(employee_id, name, email, role, team, timezone, can_interview, free_times, hr_email):
    values = {"id": employee_id, "name": name.strip(), "email": email.strip().lower(), "role": role,
              "team": team.strip(), "timezone": timezone, "can_interview": int(can_interview)}
    with engine.begin() as conn:
        if employee_id is None:
            employee_id = conn.execute(text("""
                INSERT INTO employees (name, email, role, team, timezone, can_interview)
                VALUES (:name, :email, :role, :team, :timezone, :can_interview)
                RETURNING id
            """), values).scalar_one()
            action = "Employee added"
        else:
            conn.execute(text("""
                UPDATE employees SET name = :name, email = :email, role = :role, team = :team,
                                     timezone = :timezone, can_interview = :can_interview
                WHERE id = :id
            """), values)
            action = "Employee changed"

        # The free times are replaced as a whole: remove the old rows, add the new ones.
        # Someone who can't interview has no free times
        conn.execute(text("DELETE FROM employee_availability WHERE employee_id = :id"), {"id": employee_id})
        if can_interview:
            for time in free_times:
                conn.execute(text("""
                    INSERT INTO employee_availability (employee_id, day_of_week, start_time, end_time)
                    VALUES (:id, :day_of_week, :start_time, :end_time)
                """), {"id": employee_id, **time})

    add_audit_event(hr_email, action, "employee", employee_id, name.strip())
    return employee_id


# Update: turn a person off (they stay in the database), or back on
def set_active(employee_id, active, hr_email):
    run_sql("UPDATE employees SET is_active = :active WHERE id = :id", {"id": employee_id, "active": int(active)})
    add_audit_event(hr_email, "Employee turned on" if active else "Employee turned off", "employee", employee_id)


# Create: a one-off busy time, like leave or a meeting. start and end look like "2026-11-10 14:00"
def add_busy_time(employee_id, start, end, reason, hr_email):
    run_sql("""
        INSERT INTO employee_busy_times (employee_id, start_time, end_time, reason)
        VALUES (:id, :start, :end, :reason)
    """, {"id": employee_id, "start": start, "end": end, "reason": reason.strip()})
    add_audit_event(hr_email, "Busy time added", "employee", employee_id, f"{start} to {end}")


# Delete: remove a busy time that was wrong or is over
def delete_busy_time(busy_id, employee_id, hr_email):
    run_sql("DELETE FROM employee_busy_times WHERE id = :id", {"id": busy_id})
    add_audit_event(hr_email, "Busy time removed", "employee", employee_id)
