# The HR to-do list: things the app can't solve alone. Create, read, update and delete tasks (CRUD)
from sqlalchemy import text

from app.core.audit import add_audit_event
from app.core.database.database import engine, run_sql

TASK_TYPES = ["No free slot", "Manual review", "Human requested", "Language", "Other"]


# Read: the tasks, newest first. show = "Open", "Done" or "All"
def list_tasks(show):
    with engine.begin() as conn:
        rows = conn.execute(text("""
            SELECT hr_tasks.id, hr_tasks.title, hr_tasks.task_type, hr_tasks.note, hr_tasks.status,
                   hr_tasks.created_at, hr_tasks.done_at, hr_tasks.candidate_id,
                   candidates.name AS candidate_name
            FROM hr_tasks
            LEFT JOIN candidates ON candidates.id = hr_tasks.candidate_id
            WHERE :show = 'All' OR hr_tasks.status = :show
            ORDER BY hr_tasks.id DESC
        """), {"show": show}).mappings().all()
    return [dict(row) for row in rows]


# Create: a new open task. candidate_id can be None
def add_task(title, task_type, candidate_id, note, hr_email):
    with engine.begin() as conn:
        task_id = conn.execute(text("""
            INSERT INTO hr_tasks (title, task_type, candidate_id, note)
            VALUES (:title, :task_type, :candidate_id, :note)
            RETURNING id
        """), {"title": title.strip(), "task_type": task_type, "candidate_id": candidate_id, "note": note.strip()}).scalar_one()
    add_audit_event(hr_email, "Task added", "hr_task", task_id, title.strip())


# Update: change the text of a task
def edit_task(task_id, title, task_type, note, hr_email):
    run_sql("""
        UPDATE hr_tasks SET title = :title, task_type = :task_type, note = :note
        WHERE id = :id
    """, {"id": task_id, "title": title.strip(), "task_type": task_type, "note": note.strip()})
    add_audit_event(hr_email, "Task changed", "hr_task", task_id)


# Update: mark a task done, or open again
def set_done(task_id, done, hr_email):
    if done:
        run_sql("UPDATE hr_tasks SET status = 'Done', done_at = CURRENT_TIMESTAMP WHERE id = :id", {"id": task_id})
    else:
        run_sql("UPDATE hr_tasks SET status = 'Open', done_at = NULL WHERE id = :id", {"id": task_id})
    add_audit_event(hr_email, "Task done" if done else "Task opened again", "hr_task", task_id)


# Delete: remove a task for good
def delete_task(task_id, hr_email):
    run_sql("DELETE FROM hr_tasks WHERE id = :id", {"id": task_id})
    add_audit_event(hr_email, "Task deleted", "hr_task", task_id)
