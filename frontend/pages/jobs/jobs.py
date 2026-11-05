# Jobs: see all jobs, and make a new one
import pandas as pd
import streamlit as st

from components import chip, empty_state, icon, load_page_css, page_header, pill
from levels import LEVEL_WEIGHTS

load_page_css(__file__)
page_header("Jobs", "Make a job, add its skills and upload CVs.", section="Hiring")

# Real data comes from the backend in the next step. Until then every list is empty
JOBS = []
EMPLOYEES = []

all_jobs_tab, new_job_tab = st.tabs(["All jobs", "New job"])

# ---------- Tab 1: all jobs as cards ----------
with all_jobs_tab:
    if not JOBS:
        st.html(empty_state("work", "No jobs yet", "Open the New job tab to create your first job."))
    columns = st.columns(2)
    for number, job in enumerate(JOBS):
        with columns[number % 2]:
            with st.container(key=f"card-job-{job['id']}"):
                skill_tags = "".join(chip(s["skill"], "good" if s["type"] == "Must-have" else "") for s in job["skills"])
                job_icon = "code" if job["level"] != "Team Lead" else "groups"
                st.html(f"""
                    <div class="job-card">
                        <div class="job-top">
                            <div class="job-icon">{icon(job_icon)}</div>
                            {pill("Open", "green") if job["open"] else pill("Closed", "gray")}
                        </div>
                        <h3>{job['title']}</h3>
                        <p class="job-meta">{icon('location_on')} {job['location']} &nbsp;{icon('apartment')} {job['work_type']} &nbsp;{icon('signal_cellular_alt')} {job['level']}</p>
                        <div class="job-skills">{skill_tags}</div>
                        <div class="job-bottom"><span><b>{job['candidates']}</b> candidates</span><span>{icon('person')} {job['manager']}</span></div>
                    </div>
                """)
                st.page_link("pages/candidates/candidates.py", label="See candidates", icon=":material/arrow_forward:")

# ---------- Tab 2: the new job form ----------
with new_job_tab:
    # AI Job Post Writer (Day 9 extra)
    with st.container(key="card-writer"):
        st.html("""
            <p class="section-title"><span class="mi mi-box">auto_awesome</span>AI Job Post Writer</p>
            <p class="writer-help">Type a few words. The AI writes the job post, skills, level and 5 call questions.
            You must read and edit everything before you save.</p>
        """)
        idea_col, button_col = st.columns([4, 1], vertical_alignment="bottom")
        idea_col.text_input("Your idea", placeholder="need junior Python dev, Lahore, hybrid",
                            label_visibility="collapsed")
        if button_col.button("Write it for me", icon=":material/auto_awesome:", width="stretch"):
            st.toast("MOCK: the AI writer is not connected yet.", icon=":material/auto_awesome:")

    with st.container(key="card-details"):
        st.html('<p class="section-title">Job details</p>')
        col1, col2 = st.columns(2)
        col1.text_input("Job title", placeholder="Junior Python Developer")
        level = col2.selectbox("Level", ["Junior", "Mid", "Senior", "Team Lead"])

        col1, col2, col3 = st.columns(3)
        col1.number_input("Minimum years of work", min_value=0, max_value=30, value=0)
        col2.text_input("Location", placeholder="Lahore")
        col3.selectbox("Work type", ["Office", "Remote", "Hybrid"])

        managers = [e["name"] for e in EMPLOYEES if e["role"] == "Hiring Manager"]
        st.selectbox("Hiring manager", managers, placeholder="Add a hiring manager on the Employees page first")
        st.text_area("Job post", height=160, placeholder="What the person will do, and what they need...")

        # The weights are fixed per level, so I only show them
        weights = LEVEL_WEIGHTS[level]
        weight_html = "".join(f'<div class="weight"><span>{name}</span><b>{w}%</b></div>' for name, w in weights.items())
        st.html(f'<p class="weights-title">How a {level} is scored (fixed for this level)</p>'
                f'<div class="weights">{weight_html}</div>')

    with st.container(key="card-skills"):
        st.html('<p class="section-title">Skills</p>')
        st.data_editor(
            pd.DataFrame(columns=["Skill", "Type", "Required level", "Min years"]),
            num_rows="dynamic",
            hide_index=True,
            width="stretch",
            key="new_job_skills",
            column_config={
                "Type": st.column_config.SelectboxColumn(options=["Must-have", "Nice-to-have"], required=True),
                "Required level": st.column_config.NumberColumn(min_value=1, max_value=5, step=1),
                "Min years": st.column_config.NumberColumn(min_value=0, max_value=30, step=1),
            },
        )

    with st.container(key="card-questions"):
        st.html('<p class="section-title">Call questions</p>'
                '<p class="writer-help">Job questions only. Never ask about age, religion, family or health.</p>')
        st.data_editor(
            pd.DataFrame(columns=["Question"]),
            num_rows="dynamic",
            hide_index=True,
            width="stretch",
            key="new_job_questions",
        )

    with st.container(key="card-upload"):
        st.html('<p class="section-title">Upload CVs</p>')
        files = st.file_uploader("PDF or Word files, up to 5 MB each", type=["pdf", "docx"],
                                 accept_multiple_files=True)
        if files:
            st.caption(f"{len(files)} file(s) ready. They are scored in the background after you save.")

    if st.button("Save job", type="primary", icon=":material/save:"):
        st.toast("MOCK: the job is not saved yet. FastAPI comes next.", icon=":material/save:")
