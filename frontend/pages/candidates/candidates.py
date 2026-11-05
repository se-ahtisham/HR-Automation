# Candidates: HR review screen #1. HR reads the score and decides.
# Step 1: pick a candidate from the cards. Step 2: read the details and decide.
import streamlit as st

from components import (avatar, card_title, chip, icon, icon_list, level_dots, load_page_css, page_header, part_bar, pill,
                        score_gauge, status_badge, empty_state)
from levels import LEVEL_WEIGHTS

load_page_css(__file__)

# Real data comes from the backend in the next step. Until then every list is empty
JOBS = []
CANDIDATES = []
HISTORY = []


def get_job(job_id):
    return [j for j in JOBS if j["id"] == job_id][0]


user = st.session_state.user
can_approve = user["role"] != "Hiring Manager"

if "picked_candidate" not in st.session_state:
    st.session_state.picked_candidate = None
if "blind" not in st.session_state:
    st.session_state.blind = True


# Blind Mode shows "Candidate #7". Details unlock after HR approves for screening
def is_hidden(candidate):
    locked = candidate["status"] in ["Resume Received", "Scored (HR Review)", "Needs Manual Review"]
    return st.session_state.blind and locked


def shown_name(candidate):
    return f"Candidate #{candidate['id']}" if is_hidden(candidate) else candidate["name"]


# ======================= Step 2: one candidate's details =======================
if st.session_state.picked_candidate is not None:
    c = [p for p in CANDIDATES if p["id"] == st.session_state.picked_candidate][0]
    job = get_job(c["job_id"])

    if st.button("Back to all candidates", icon=":material/arrow_back:", type="tertiary"):
        st.session_state.picked_candidate = None
        st.rerun()

    # ---------- Top card: who, and the score ----------
    with st.container(key="card-head"):
        info_col, gauge_col = st.columns([2.4, 1], vertical_alignment="center")
        with info_col:
            if is_hidden(c):
                contact = f'<p class="contact">{icon("lock")} Name and contact details unlock after you approve for screening.</p>'
            else:
                contact = f'<p class="contact">{icon("mail")} {c["email"]} &nbsp;·&nbsp; {icon("call")} {c["phone"]}</p>'
            st.html(f"""
                <div class="head">
                    {avatar(c['name'], 'lg', hidden=is_hidden(c))}
                    <div>
                        <h2 class="detail-name">{shown_name(c)}</h2>
                        <p class="detail-meta">{job['title']} · {job['level']}</p>
                        {status_badge(c['status'])}
                        {contact}
                    </div>
                </div>
            """)
        with gauge_col:
            if c["score"] is not None:
                st.html(score_gauge(c["score"]))

    # A CV that couldn't be read has no score, so a human must check it
    if c["score"] is None:
        st.error(f"Needs Manual Review: {c['note']}. Ask the candidate for a new file.", icon=":material/error:")
        st.stop()

    if c["trick_lines"]:
        found = ", ".join(f'"{line}"' for line in c["trick_lines"])
        st.warning(f"Trick lines found in the CV: {found}. They were ignored, and the score did not change.",
                   icon=":material/warning:")

    detail_col, decide_col = st.columns([2, 1], gap="medium")

    with detail_col:
        score_tab, skills_tab, notes_tab, history_tab = st.tabs(["Score", "Skills", "Notes", "History"])

        with score_tab:
            with st.container(key="card-score"):
                weights = LEVEL_WEIGHTS[job["level"]]
                st.html('<p class="section-title">Part scores</p>' +
                        "".join(part_bar(name, score, weights[name]) for name, score in c["parts"].items()))
                st.html('<p class="section-title" style="margin-top:1.2rem">Proof from the CV</p>' +
                        "".join(f'<blockquote class="proof-line">{line}</blockquote>' for line in c["proof_lines"]))

        with skills_tab:
            with st.container(key="card-skills"):
                needed = {s["skill"]: s for s in job["skills"]}
                rows = ""
                for s in c["skill_scores"]:
                    need = needed.get(s["skill"], {"type": "—", "required_level": 0})
                    low = s["level"] < need["required_level"]
                    if not low:
                        flag = pill("Meets", "green")
                    elif need["type"] == "Must-have":
                        flag = pill("Must-have is low", "red")
                    else:
                        flag = pill("Below", "amber")
                    rows += f"""
                        <div class="skill-row">
                            <div><b>{s['skill']}</b><small>{need['type']}</small></div>
                            <div>{level_dots(s['level'], need['required_level'])}</div>
                            <div>{flag}</div>
                            <div class="proof">“{s['proof']}”</div>
                        </div>
                    """
                st.html(rows + '<p class="hint">The orange ring shows the needed level. '
                               'A low must-have is only a warning, never a reject.</p>')

        with notes_tab:
            with st.container(key="card-notes"):
                col1, col2, col3 = st.columns(3)
                col1.html(card_title("thumb_up", "Strengths", "mi-green") + icon_list(c["strengths"], "check"))
                col2.html(card_title("search", "Weak points", "mi-amber") + icon_list(c["weak_points"], "remove"))
                missing = "".join(chip(s, "missing") for s in c["missing_skills"]) or "Nothing is missing."
                col3.html(card_title("block", "Missing skills", "mi-red") + missing)
                email = pill("Sent (MOCK)", "green") if c["email_sent"] else pill("Not sent", "gray")
                st.html(f'<p class="email-line">CV Match Score email: {email}</p>')

        with history_tab:
            with st.container(key="card-history"):
                items = "".join(
                    f'<li><span class="time">{h["time"]}</span><b>{h["who"]}</b>: {h["what"]}</li>' for h in HISTORY
                )
                st.html(f'<ul class="history">{items}</ul>')

    # ---------- HR decision (HR stop #1), always next to the details ----------
    with decide_col:
        with st.container(key="card-decision"):
            st.html('<p class="section-title">Your decision</p>'
                    '<p class="hint" style="margin-top:-0.4rem">The AI only advises. Please write why.</p>')
            if not can_approve:
                st.info("A Hiring Manager can see candidates, but can't approve or decline.", icon=":material/lock:")
            reason = st.text_area("Reason", placeholder="Why did you decide this?", height=110,
                                  disabled=not can_approve)
            approve = st.button("Approve for screening", type="primary", icon=":material/check:",
                                width="stretch", disabled=not can_approve)
            col1, col2 = st.columns(2)
            decline = col1.button("Decline", icon=":material/close:", width="stretch", disabled=not can_approve)
            change = col2.button("Change", icon=":material/edit:", width="stretch", disabled=not can_approve)
            if approve or decline or change:
                if reason.strip():
                    st.toast("MOCK: your decision is not saved yet.", icon=":material/check_circle:")
                else:
                    st.error("Please write a reason first.")
    st.stop()


# ======================= Step 1: all candidates as cards =======================
page_header("Candidates", "Best score first. Open a card to read the proof and decide.", section="Hiring")

if not JOBS:
    st.html(empty_state("group", "No candidates yet", "Create a job and upload CVs. Each CV is scored and shows here."))
    st.stop()

filter_col, grid_col = st.columns([1.15, 3.4], gap="medium")

# ---------- Left: the filter panel ----------
with filter_col:
    with st.container(key="card-filter"):
        st.html('<p class="filter-title">Filter</p><p class="filter-label">Job</p>')
        job_titles = [job["title"] for job in JOBS]
        picked_title = st.radio("Job", job_titles, label_visibility="collapsed")
        job = [j for j in JOBS if j["title"] == picked_title][0]
        people = [c for c in CANDIDATES if c["job_id"] == job["id"]]

        st.html('<p class="filter-label">Status</p>')
        statuses = sorted({c["status"] for c in people})
        shown_statuses = [s for s in statuses if st.checkbox(f"{s} · {len([c for c in people if c['status'] == s])}",
                                                             value=True, key=f"status_{s}")]

        st.html('<p class="filter-label">Minimum score</p>')
        min_score = st.slider("Minimum score", 0, 100, 0, step=5, label_visibility="collapsed")

        st.html('<p class="filter-label">Privacy</p>')
        # The toggle isn't on screen in Step 2, so I keep its value in my own key
        st.session_state.blind = st.toggle(":material/visibility_off: Blind Mode", value=st.session_state.blind,
                                           help="Hides name, email, phone and other personal details.")

# Keep the people that pass the filters. A candidate with no score always shows, so a human sees them
people = [c for c in people if c["status"] in shown_statuses]
people = [c for c in people if c["score"] is None or c["score"] >= min_score]
people.sort(key=lambda c: c["score"] if c["score"] is not None else -1, reverse=True)

# ---------- Right: the cards, 3 in a row ----------
with grid_col:
    st.html(f'<p class="grid-title">{job["title"]} <span>{len(people)} candidates</span></p>')
    if not people:
        st.html('<div class="empty">No candidates match these filters.</div>')

    columns = st.columns(3)
    for number, c in enumerate(people):
        with columns[number % 3]:
            with st.container(key=f"card-person-{c['id']}"):
                needed = {s["skill"]: s["required_level"] for s in job["skills"]}
                tags = ""
                for s in c["skill_scores"]:
                    kind = "good" if s["level"] >= needed.get(s["skill"], 0) else "missing"
                    tags += chip(s["skill"], kind)
                if c["score"] is None:
                    score = '<span class="score-pill score-none">No score</span>'
                    tags = chip(c["note"])
                else:
                    score = f'<span class="score-pill">{c["score"]}<small>/100</small></span>'
                warning = f'<span class="trick-dot" title="Trick lines found">{icon("warning")}</span>' if c["trick_lines"] else ""
                st.html(f"""
                    <div class="person-top">{avatar(c['name'], 'md', hidden=is_hidden(c))}{score}</div>
                    <p class="person-name">{shown_name(c)} {warning}</p>
                    <p class="person-job">{job['title']}</p>
                    <div class="tags">{tags}</div>
                    {status_badge(c['status'])}
                """)
                if st.button("Review", key=f"open_{c['id']}", type="primary", width="stretch"):
                    st.session_state.picked_candidate = c["id"]
                    st.rerun()
