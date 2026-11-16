# The start file of my web app. Run it from the project root:
#   uv run streamlit run frontend/app.py
import sys
from pathlib import Path

import streamlit as st

# The pages call my Python code in app/ directly, so the project folder must be on Python's import path.
# It goes first, so "import app.core..." finds the app/ folder and not this app.py file
PROJECT_ROOT = str(Path(__file__).parent.parent)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.core.candidates import delete_old_candidates
from components import FRONTEND, add_css, avatar

st.set_page_config(page_title="Nexora Hire", page_icon=":material/auto_awesome:", layout="wide")
add_css(FRONTEND / "base.css")

# Everyone starts logged out. The login page fills this in
if "user" not in st.session_state:
    st.session_state.user = None

# All my pages. Each one is a .py file with its own .css file next to it
login = st.Page("pages/login/login.py", title="Log in", icon=":material/login:")
dashboard = st.Page("pages/dashboard/dashboard.py", title="Dashboard", icon=":material/space_dashboard:", default=True)
jobs = st.Page("pages/jobs/jobs.py", title="Jobs", icon=":material/work:")
candidates = st.Page("pages/candidates/candidates.py", title="Candidates", icon=":material/group:")
call_results = st.Page("pages/call_results/call_results.py", title="Call results", icon=":material/call:")
interviews = st.Page("pages/interviews/interviews.py", title="Interviews", icon=":material/event:")
score_cvs = st.Page("pages/score_cvs/score_cvs.py", title="Upload & score CVs", icon=":material/upload_file:")
todo = st.Page("pages/todo/todo.py", title="HR to-do list", icon=":material/checklist:")
employees = st.Page("pages/employees/employees.py", title="Employees", icon=":material/badge:")
settings = st.Page("pages/settings/settings.py", title="Settings", icon=":material/settings:")

ask_questions = st.Page("pages/ask_questions/ask_questions.py", title="Ask questions", icon=":material/record_voice_over:")

user = st.session_state.user

# A candidate's secret link (?token=...): only the Ask questions page, never the HR pages
if user is None and st.query_params.get("token"):
    st.navigation([ask_questions], position="hidden").run()
    st.stop()

# Not logged in: show only the login page
if user is None:
    st.navigation([login], position="hidden").run()
    st.stop()

# Only HR logs in, so there is one menu with every page
menu = {
    "Overview": [dashboard],
    "Hiring": [jobs, score_cvs, candidates, call_results, interviews],
    "Tools": [todo],
    "Manage": [employees, settings],
}

# position="hidden" hides Streamlit's own menu, so I can draw my own below
page = st.navigation(menu, position="hidden")

with st.sidebar:
    st.logo(FRONTEND / "logo.svg", size="large")

    # The profile at the top: small, so the menu has room
    st.html(f"""
        <div class="profile">
            {avatar(user['name'], 'md')}
            <div>
                <p class="name">{user['name']}</p>
                <p class="role">{user['role']}</p>
            </div>
        </div>
    """)

    # My own menu. The page I am on gets "-active" in its key, so CSS can make it brighter
    with st.container(key="side-nav"):
        for number, (group, group_pages) in enumerate(menu.items()):
            first = "first" if number == 0 else ""
            st.html(f'<p class="nav-group {first}">{group}</p>')
            for menu_page in group_pages:
                slug = menu_page.title.lower().replace(" ", "-")
                active = "-active" if menu_page.title == page.title else ""
                with st.container(key=f"nav-{slug}{active}"):
                    st.page_link(menu_page)

    # Blind Review Mode, for every page. On by default: HR judges the skills first, then sees who it is
    st.session_state.blind = st.toggle("Blind Mode", value=st.session_state.get("blind", True), key="blind_switch",
                                       help="Hides name, email and phone until you approve a candidate for calling.")

    with st.container(key="logout"):
        if st.button("Log out", icon=":material/logout:", width="stretch"):
            st.session_state.user = None
            st.rerun()

# Privacy: once per login, delete candidates older than the "keep data" days (90 by default)
if "old_data_cleaned" not in st.session_state:
    delete_old_candidates()
    st.session_state.old_data_cleaned = True

page.run()
