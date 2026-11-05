# HR to-do list: problems the app can't solve on its own
import streamlit as st

from components import empty_state, load_page_css, page_header, pill

load_page_css(__file__)
page_header("HR to-do list", "Things that need a human: no free time, a locked file, a request for a person.", section="Tools")

# Each task type gets a color
TYPE_COLORS = {
    "No free slot": "amber",
    "Manual review": "red",
    "Human requested": "violet",
    "Language": "blue",
}

# Real data comes from the backend in the next step. Until then the list is empty
TODOS = []

show = st.segmented_control("Show", ["Open", "Done", "All"], default="Open")

if not TODOS:
    st.html(empty_state("task_alt", "Nothing to do", "Problems the app can't solve alone show here, like a locked CV."))

for number, task in enumerate(TODOS):
    if show == "Open" and task["done"]:
        continue
    if show == "Done" and not task["done"]:
        continue

    with st.container(key=f"card-task-{number}"):
        check_col, text_col, button_col = st.columns([0.35, 5, 0.9], vertical_alignment="center", gap="small")
        check_col.checkbox("Done", value=task["done"], key=f"task_{number}", label_visibility="collapsed")
        text_col.html(f"""
            <p class="task-text">{task['task']}</p>
            <p class="task-meta">{pill(task['type'], TYPE_COLORS[task['type']])} · {task['candidate']}</p>
        """)
        button_col.page_link("pages/candidates/candidates.py", label="Open", icon=":material/arrow_forward:")
