# Upload & score CVs: pick a saved job, upload a candidate's CV, and score it with that job's level and skills.
# The name and email are read from the CV. The candidate, the file and the score are saved in the database
from html import escape

import streamlit as st

from app.agents.resume_scoring.reader import FileProblem
from app.core.candidates import approve_for_calling
from app.core.cv_scoring import job_skills, score_cv_for_job
from app.core.database.database import get_one
from app.core.jobs import list_jobs
from components import FRONTEND, add_css, chip, empty_state, icon, is_hidden, load_page_css, page_header, shown_name, status_badge
from score_view import send_score_button, show_email_preview, show_score_result

load_page_css(__file__)
add_css(FRONTEND / "score_view.css")
page_header("Upload & score CVs", "Pick a job, upload a candidate's CV, and let Agent 1 score it for that job.", section="Hiring")

user = st.session_state.user
jobs = list_jobs()

if not jobs:
    st.html(empty_state("work", "No jobs yet", "Create a job first. Each job has its own level and skills, so each CV is scored for one job."))
    st.page_link("pages/jobs/jobs.py", label="Create a job", icon=":material/add:")
    st.stop()

# The picked job is kept by its id, so it stays the same after every click. The newest job is picked first
job_ids = [job["id"] for job in jobs]
if st.session_state.get("cv_job_id") not in job_ids:
    st.session_state.cv_job_id = job_ids[0]

# A number in the uploader key. Making it bigger after a score gives an empty box for the next CV
if "cv_form" not in st.session_state:
    st.session_state.cv_form = 0

# ---------- Step 1: the job, as cards. Click one to pick it ----------
st.html('<p class="step"><span>1</span>Pick the job</p>')
columns = st.columns(3, gap="small")
for number, job in enumerate(jobs):
    picked = job["id"] == st.session_state.cv_job_id
    with columns[number % 3]:
        with st.container(key=f"job-card-{job['id']}" + ("-picked" if picked else "")):
            location = escape(job["location"]) if job["location"] else "No location"
            st.html(f"""
                <p class="job-title">{escape(job['title'])}</p>
                <p class="job-meta">{icon('signal_cellular_alt')} {job['level']} &nbsp; {icon('location_on')} {location}
                   &nbsp; {icon('apartment')} {job['work_type']}</p>
                <p class="job-meta">{len(job['skills'])} skills · {job['candidate_count']} candidates</p>
            """)
            if st.button("Picked" if picked else "Pick this job", key=f"pick_{job['id']}", width="stretch",
                         icon=":material/check_circle:" if picked else None, type="primary" if picked else "secondary"):
                st.session_state.cv_job_id = job["id"]
                st.rerun()

job = next(j for j in jobs if j["id"] == st.session_state.cv_job_id)

# ---------- Step 2: the CV. The name and email come from the CV ----------
with st.container(key="card-candidate"):
    st.html(f'<p class="step"><span>2</span>Upload the CV for <b>{escape(job["title"])}</b></p>')
    skill_tags = "".join(chip(escape(s["name"]) + f" · {s['required_level']}", "good" if s["skill_type"] == "Must-have" else "")
                         for s in job["skills"])
    st.html(f'<div class="job-summary"><p class="label">Skills checked (with the needed level)</p><div>{skill_tags}</div></div>')
    cv_file = st.file_uploader("CV (PDF or Word). The name and email are read from it.", type=["pdf", "docx"],
                               key=f"cv_file_{st.session_state.cv_form}")

# ---------- The Score button: the only place that calls the AI ----------
if st.button("Score this CV", type="primary", icon=":material/auto_awesome:", width="stretch"):
    if cv_file is None:
        st.error("Please upload the CV.", icon=":material/error:")
    else:
        with st.spinner("Reading the CV and scoring it for this job. This takes about 10 to 30 seconds..."):
            try:
                candidate_id, result = score_cv_for_job(job, cv_file.name, cv_file.getvalue(), user["email"])
                # Keep everything, so it stays when the page reruns
                st.session_state.cv_scored = {"candidate_id": candidate_id, "result": result, "job_title": job["title"],
                                              "level": job["level"], "skills": job_skills(job)}
                st.session_state.cv_form += 1
                st.rerun()
            except FileProblem as error:
                st.error(str(error), icon=":material/error:")

scored = st.session_state.get("cv_scored")
if not scored:
    st.html(f'<div class="empty-state">{icon("upload_file", "empty-icon")}<br>'
            'Pick a job, upload the CV and click <b>Score this CV</b>.</div>')
    st.stop()

# ---------- Saved: who (read from the CV), and where they are now ----------
person = get_one("SELECT name, email, phone, current_status FROM candidates WHERE id = :id", {"id": scored["candidate_id"]})
# Blind Mode: until HR approves for calling, show "Candidate #7" and hide the contact details
hidden = is_hidden(person.current_status)
name = shown_name(scored["candidate_id"], person.name, person.current_status)
contact = "Details hidden (Blind Mode)" if hidden else f"{escape(person.email or 'No email')} · {escape(person.phone or 'No phone')}"
with st.container(key="card-saved"):
    info_col, button_col = st.columns([3, 1.3], vertical_alignment="center")
    info_col.html(f"""
        <p class="saved-name">{escape(name)} <small>· {contact} · Candidate #{scored['candidate_id']}</small></p>
        <p class="saved-meta">{escape(scored['job_title'])} &nbsp;{status_badge(person.current_status)}</p>
    """)
    # HR stop #1: approving moves the candidate to Candidates, where the script agent can call them
    if person.current_status == "Scored (HR Review)":
        if button_col.button("Approved for calling", type="primary", icon=":material/check:", width="stretch"):
            approve_for_calling(scored["candidate_id"], user["email"], blind=hidden)
            st.rerun()
    elif person.current_status == "Approved for Calling":
        button_col.page_link("pages/candidates/candidates.py", label="Go to Candidates", icon=":material/group:")
    # The CV Match Score email (once per candidate)
    if scored["result"] is not None:
        with button_col:
            send_score_button(scored["candidate_id"], user["email"])

if scored["result"] is not None:
    show_email_preview(scored["candidate_id"], hidden)
    show_score_result(scored["result"], scored["level"], scored["skills"], name)
