# HR to-do list: things the app can't solve on its own. HR can add, read, change, finish and delete tasks
from html import escape

import streamlit as st

from app.core.candidates import list_candidates
from app.core.hr_tasks import TASK_TYPES, add_task, delete_task, edit_task, list_tasks, set_done
from components import empty_state, load_page_css, page_header, pill

load_page_css(__file__)
page_header("HR to-do list", "Things that need a human: no free time, a locked file, a request for a person.", section="Tools")

user = st.session_state.user

# Each task type gets a color
TYPE_COLORS = {"No free slot": "amber", "Manual review": "red", "Human requested": "violet", "Language": "blue", "Other": "gray"}

# The candidates HR can link a task to. None = not about one candidate
candidates = {c["id"]: c["name"] for c in list_candidates()}

# A number in the form keys. Making it bigger after saving gives empty boxes
if "task_form" not in st.session_state:
    st.session_state.task_form = 0
form = st.session_state.task_form

# ---------- Create: add a new task ----------
with st.expander("Add a task", icon=":material/add_task:"):
    title = st.text_input("Task *", placeholder="Call Ayesha back about the interview time", key=f"new_title_{form}")
    type_col, candidate_col = st.columns(2)
    task_type = type_col.selectbox("Type", TASK_TYPES, key=f"new_type_{form}")
    candidate_id = candidate_col.selectbox("Candidate (optional)", list(candidates), format_func=lambda i: candidates[i],
                                           index=None, placeholder="Not about one candidate", key=f"new_candidate_{form}")
    note = st.text_area("Note", placeholder="Anything to remember...", key=f"new_note_{form}")
    if st.button("Add task", type="primary", icon=":material/add:"):
        if title.strip():
            add_task(title, task_type, candidate_id, note, user["email"])
            st.session_state.task_form += 1
            st.rerun()
        else:
            st.error("Please write the task.", icon=":material/error:")

# ---------- Read: the list ----------
show = st.segmented_control("Show", ["Open", "Done", "All"], default="Open", label_visibility="collapsed") or "All"
tasks = list_tasks(show)

if not tasks:
    st.html(empty_state("task_alt", "Nothing to do", "Add a task above. Problems the app can't solve alone show here too."))

for task in tasks:
    done = task["status"] == "Done"
    with st.container(key=f"card-task-{task['id']}"):
        check_col, text_col, edit_col, delete_col = st.columns([0.35, 5, 0.9, 0.9], vertical_alignment="center", gap="small")

        # Update: tick = done, untick = open again
        ticked = check_col.checkbox("Done", value=done, key=f"done_{task['id']}", label_visibility="collapsed")
        if ticked != done:
            set_done(task["id"], ticked, user["email"])
            st.rerun()

        who = escape(task["candidate_name"]) if task["candidate_name"] else "No candidate"
        note = f'<p class="task-note">{escape(task["note"])}</p>' if task["note"] else ""
        text_col.html(f"""
            <p class="task-text {'task-done' if done else ''}">{escape(task['title'])}</p>
            <p class="task-meta">{pill(task['task_type'], TYPE_COLORS.get(task['task_type'], 'gray'))} · {who} · {task['created_at'][:16]}</p>
            {note}
        """)

        # Update: change the text
        with edit_col.popover("", icon=":material/edit:", help="Change"):
            new_title = st.text_input("Task", value=task["title"], key=f"title_{task['id']}")
            new_type = st.selectbox("Type", TASK_TYPES, index=TASK_TYPES.index(task["task_type"]), key=f"type_{task['id']}")
            new_note = st.text_area("Note", value=task["note"] or "", key=f"note_{task['id']}")
            if st.button("Save", type="primary", key=f"save_{task['id']}"):
                edit_task(task["id"], new_title, new_type, new_note, user["email"])
                st.rerun()

        # Delete: asks first, so one wrong click doesn't delete it
        with delete_col.popover("", icon=":material/delete:", help="Delete"):
            st.write("Delete this task for good?")
            if st.button("Yes, delete", type="primary", key=f"delete_{task['id']}"):
                delete_task(task["id"], user["email"])
                st.rerun()
