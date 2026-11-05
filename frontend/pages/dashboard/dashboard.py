# Dashboard: the big picture of all jobs and candidates
import streamlit as st

from components import avatar, empty_state, load_page_css, score_gauge, stat_tile, status_badge, svg_image

load_page_css(__file__)

# Real data comes from the backend in the next step. Until then every list is empty
JOBS = []
CANDIDATES = []
INTERVIEWS = []
TODOS = []
ACTIVITY = []

user = st.session_state.user
waiting = [c for c in CANDIDATES if "(HR Review)" in c["status"]]
open_todos = [t for t in TODOS if not t["done"]]


def job_title(job_id):
    return next((j["title"] for j in JOBS if j["id"] == job_id), "")


# ---------- Purple welcome banner with the next thing to do ----------
with st.container(key="hero"):
    text_col, art_col = st.columns([2.2, 1], vertical_alignment="center")
    with text_col:
        if waiting:
            title = f"{len(waiting)} candidates are waiting for your decision"
            sub = "The AI has scored them. Read the proof, then approve or decline."
        else:
            title = "Let's start hiring"
            sub = "Create your first job, then upload CVs. The AI scores them, and you decide."
        st.html(f"""
            <p class="hero-hi">Welcome, {user['name'].split()[0]}</p>
            <h2 class="hero-title">{title}</h2>
            <p class="hero-sub">{sub}</p>
        """)
        # A row with an even gap between the 2 buttons
        with st.container(horizontal=True, gap="small"):
            if waiting:
                st.page_link("pages/candidates/candidates.py", label="Review candidates", icon=":material/arrow_forward:")
            else:
                st.page_link("pages/jobs/jobs.py", label="Create a job", icon=":material/add:")
            st.page_link("pages/score_cvs/score_cvs.py", label="Score a CV", icon=":material/upload_file:")
    with art_col:
        st.html(svg_image("""
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 150">
                <rect x="40" y="10" width="100" height="125" rx="12" fill="white" opacity="0.95"/>
                <rect x="55" y="30" width="50" height="8" rx="4" fill="#C4B5FD"/>
                <rect x="55" y="48" width="70" height="6" rx="3" fill="#E4DEFF"/>
                <rect x="55" y="62" width="60" height="6" rx="3" fill="#E4DEFF"/>
                <rect x="55" y="76" width="66" height="6" rx="3" fill="#E4DEFF"/>
                <rect x="55" y="98" width="40" height="18" rx="9" fill="#6C5CE7"/>
                <circle cx="138" cy="98" r="26" fill="none" stroke="white" stroke-width="9"/>
                <rect x="153" y="115" width="10" height="34" rx="5" fill="white" transform="rotate(-40 158 132)"/>
                <circle cx="138" cy="98" r="18" fill="#A78BFA" opacity="0.6"/>
            </svg>
        """, "hero-art"))

# ---------- 4 pastel tiles ----------
col1, col2, col3, col4 = st.columns(4)
col1.html(stat_tile("Open jobs", len(JOBS), "work", "pink"))
col2.html(stat_tile("Candidates", len(CANDIDATES), "group", "cyan"))
col3.html(stat_tile("Waiting for you", len(waiting), "hourglass_top", "salmon"))
col4.html(stat_tile("Interviews", len(INTERVIEWS), "event", "lilac"))

# ---------- Candidates table, and the side cards ----------
left, right = st.columns([1.75, 1])

with left:
    with st.container(key="card-candidates"):
        # Title on the left, "See all" on the right, both on one line
        with st.container(horizontal=True, horizontal_alignment="distribute", vertical_alignment="center"):
            st.html('<p class="section-title">Latest candidates</p>', width="content")
            st.page_link("pages/candidates/candidates.py", label="See all", icon=":material/arrow_forward:")
        if not CANDIDATES:
            st.html(empty_state("group", "No candidates yet", "Create a job and upload CVs to see candidates here."))
        else:
            rows = ""
            for c in CANDIDATES:
                if c["score"] is None:
                    score = '<span class="no-score">No score</span>'
                else:
                    score = f"""
                        <div class="mini-score">
                            <b>{c['score']}</b>
                            <div class="mini-track"><div style="width:{c['score']}%"></div></div>
                        </div>
                    """
                rows += f"""
                    <tr>
                        <td><div class="who">{avatar(c['name'], 'sm')}<div><b>{c['name']}</b><small>{job_title(c['job_id'])}</small></div></div></td>
                        <td>{score}</td>
                        <td>{status_badge(c['status'])}</td>
                    </tr>
                """
            st.html(f"""
                <table class="nice-table">
                    <thead><tr><th>Candidate</th><th>Score</th><th>Status</th></tr></thead>
                    <tbody>{rows}</tbody>
                </table>
            """)

with right:
    with st.container(key="card-gauge"):
        st.html('<p class="section-title">Average match</p>')
        # The average score of everyone who has one
        scores = [c["score"] for c in CANDIDATES if c["score"] is not None]
        if scores:
            st.html(score_gauge(round(sum(scores) / len(scores)), "All candidates"))
        else:
            st.html(empty_state("speed", "No scores yet", "The average shows after the first CV is scored."))

        # How many candidates are at each step
        if CANDIDATES:
            steps = [
                ("Scored", ["Scored (HR Review)"]),
                ("Screening", ["Approved for Calling", "Screening Pending", "Screening Completed (HR Review)"]),
                ("Interview", ["Approved for Interview", "Interview Proposed", "Interview Scheduled"]),
                ("Manual review", ["Needs Manual Review"]),
            ]
            bars = ""
            for name, statuses in steps:
                count = len([c for c in CANDIDATES if c["status"] in statuses])
                percent = count / len(CANDIDATES) * 100
                bars += f"""
                    <div class="step">
                        <div class="step-top"><span>{name}</span><b>{count}</b></div>
                        <div class="step-track"><div style="width:{percent}%"></div></div>
                    </div>
                """
            st.html(f'<div class="steps">{bars}</div>')

    with st.container(key="card-todo"):
        st.html(f'<p class="section-title">To-do <span class="count">{len(open_todos)}</span></p>')
        if not open_todos:
            st.html('<p class="nothing">Nothing to do right now.</p>')
        for t in open_todos:
            st.checkbox(t["task"], key=f"dash_todo_{t['task']}")
        st.page_link("pages/todo/todo.py", label="See all tasks", icon=":material/arrow_forward:")

# ---------- Recent activity ----------
with st.container(key="card-activity"):
    st.html('<p class="section-title">Recent activity</p>')
    if not ACTIVITY:
        st.html('<p class="nothing">No activity yet.</p>')
    else:
        items = ""
        for a in ACTIVITY:
            items += f'<li><span class="time">{a["time"]}</span><p><b>{a["who"]}</b> {a["what"]}</p></li>'
        st.html(f'<ul class="timeline">{items}</ul>')
