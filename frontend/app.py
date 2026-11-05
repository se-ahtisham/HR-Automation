# The start file of my web app. Run it from the project root:
#   uv run streamlit run frontend/app.py
import streamlit as st

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
screening = st.Page("pages/screening/screening.py", title="Screening calls", icon=":material/call:")
interviews = st.Page("pages/interviews/interviews.py", title="Interviews", icon=":material/event:")
score_test = st.Page("pages/score_test/score_test.py", title="Score test", icon=":material/science:")
chat = st.Page("pages/chat/chat.py", title="Ask your candidates", icon=":material/forum:")
todo = st.Page("pages/todo/todo.py", title="HR to-do list", icon=":material/checklist:")
employees = st.Page("pages/employees/employees.py", title="Employees", icon=":material/badge:")
settings = st.Page("pages/settings/settings.py", title="Settings", icon=":material/settings:")
templates = st.Page("pages/templates/templates.py", title="Templates", icon=":material/mail:")

user = st.session_state.user

# Not logged in: show only the login page
if user is None:
    st.navigation([login], position="hidden").run()
    st.stop()

# Only HR logs in, so there is one menu with every page
menu = {
    "Overview": [dashboard],
    "Hiring": [jobs, candidates, screening, interviews],
    "Tools": [score_test, chat, todo],
    "Manage": [employees, settings, templates],
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

    st.html("""
        <div class="side-tip">
            <span class="mi">verified_user</span>
            <div><b>AI advises, you decide</b>Every step needs a person.</div>
        </div>
    """)

    with st.container(key="logout"):
        if st.button("Log out", icon=":material/logout:", width="stretch"):
            st.session_state.user = None
            st.rerun()

page.run()
