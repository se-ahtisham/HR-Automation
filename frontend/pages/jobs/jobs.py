# Jobs: see all jobs, and make a new one. Jobs are saved in the database (jobs, job_skills).
# No call questions: the script agent asks the same questions for every job
from html import escape

import pandas as pd
import streamlit as st

from app.agents.job_writer.agent import write_job_post
from app.core.jobs import LEVELS, SKILL_TYPES, WORK_TYPES, check_new_job, list_employee_names, list_jobs, save_job
from components import chip, empty_state, icon, load_page_css, page_header, pill
from levels import LEVEL_WEIGHTS

load_page_css(__file__)
page_header("Jobs", "Make a job with its level and skills.", section="Hiring")

user = st.session_state.user

# A number in every form key. Making it bigger after a save gives a fresh, empty form
if "job_form" not in st.session_state:
    st.session_state.job_form = 0
form = st.session_state.job_form

# A message to show once, after the page reruns
if st.session_state.get("job_saved"):
    st.toast(st.session_state.job_saved, icon=":material/check_circle:")
    st.session_state.job_saved = None

jobs = list_jobs()

all_jobs_tab, new_job_tab = st.tabs([f"All jobs ({len(jobs)})", "New job"])

# ---------- Tab 1: all jobs as cards, from the database ----------
with all_jobs_tab:
    if not jobs:
        st.html(empty_state("work", "No jobs yet", "Open the New job tab to create your first job."))
    columns = st.columns(2)
    for number, job in enumerate(jobs):
        with columns[number % 2]:
            with st.container(key=f"card-job-{job['id']}"):
                skill_tags = "".join(chip(escape(s["name"]), "good" if s["skill_type"] == "Must-have" else "")
                                     for s in job["skills"])
                job_icon = "groups" if job["level"] == "Team Lead" else "code"
                status = pill("Open", "green") if job["status"] == "Open" else pill(job["status"], "gray")
                location = escape(job["location"]) if job["location"] else "No location"
                manager = escape(job["manager_name"]) if job["manager_name"] else "No hiring manager"
                st.html(f"""
                    <div class="job-card">
                        <div class="job-top">
                            <div class="job-icon">{icon(job_icon)}</div>
                            {status}
                        </div>
                        <h3>{escape(job['title'])}</h3>
                        <p class="job-meta">{icon('location_on')} {location} &nbsp;{icon('apartment')} {job['work_type']} &nbsp;{icon('signal_cellular_alt')} {job['level']}</p>
                        <div class="job-skills">{skill_tags}</div>
                        <div class="job-bottom"><span><b>{job['candidate_count']}</b> candidates</span><span>{icon('person')} {manager}</span></div>
                    </div>
                """)
                with st.expander("Job post"):
                    st.markdown(job["job_description"])

# ---------- Tab 2: the new job form ----------
with new_job_tab:
    # AI Job Post Writer: a short idea -> the whole form filled in. HR must read and edit it before saving
    with st.container(key="card-writer"):
        st.html("""
            <p class="section-title"><span class="mi mi-box">auto_awesome</span>AI Job Post Writer</p>
            <p class="writer-help">Type a few words. The AI fills in the form below: job post, level and skills.
            You must read and edit everything before you save.</p>
        """)
        idea_col, button_col = st.columns([4, 1], vertical_alignment="bottom")
        idea = idea_col.text_input("Your idea", placeholder="need junior Python dev, Lahore, hybrid",
                                   label_visibility="collapsed", key=f"idea_{form}")
        if button_col.button("Write it for me", icon=":material/auto_awesome:", width="stretch"):
            if not idea.strip():
                st.error("Type a few words about the job first.", icon=":material/error:")
            else:
                with st.spinner("The AI is writing the job..."):
                    new_draft = write_job_post(idea)
                if new_draft is None:
                    st.error("The AI failed 3 times. Please try again in a minute, or fill in the form yourself.",
                             icon=":material/error:")
                else:
                    # Keep the draft, and use new form keys, so every box starts with the AI's text
                    st.session_state.job_draft = new_draft.model_dump()
                    st.session_state.job_form += 1
                    st.rerun()

    # The AI's draft, or empty boxes when there is no draft
    draft = st.session_state.get("job_draft") or {}
    if draft:
        st.info("The AI filled in this form. Please read and change anything before you save.", icon=":material/edit_note:")

    with st.container(key="card-details"):
        st.html('<p class="section-title">Job details</p>')
        col1, col2 = st.columns(2)
        title = col1.text_input("Job title *", value=draft.get("title", ""), placeholder="Junior Python Developer",
                                key=f"title_{form}")
        level = col2.selectbox("Level *", LEVELS, index=LEVELS.index(draft["level"]) if draft else 0, key=f"level_{form}")

        col1, col2, col3 = st.columns(3)
        min_experience = col1.number_input("Minimum years of work", min_value=0, max_value=30,
                                           value=draft.get("min_experience", 0), key=f"years_{form}")
        location = col2.text_input("Location", value=draft.get("location", ""), placeholder="Lahore", key=f"location_{form}")
        work_type = col3.selectbox("Work type *", WORK_TYPES, index=WORK_TYPES.index(draft["work_type"]) if draft else 0,
                                   key=f"work_{form}")

        # Hiring manager is optional. People come from the Employees page
        managers = list_employee_names()
        manager_names = {m["name"]: m["id"] for m in managers}
        manager = st.selectbox("Hiring manager (optional)", list(manager_names), index=None,
                               placeholder="Add employees on the Employees page to pick one", key=f"manager_{form}")

        description = st.text_area("Job post *", value=draft.get("job_post", ""), height=220, key=f"description_{form}",
                                   placeholder="What the person will do, and what they need...")

        # The weights are fixed per level, so I only show them
        weights = LEVEL_WEIGHTS[level]
        weight_html = "".join(f'<div class="weight"><span>{name}</span><b>{w}%</b></div>' for name, w in weights.items())
        st.html(f'<p class="weights-title">How a {level} is scored (fixed for this level)</p>'
                f'<div class="weights">{weight_html}</div>')

    with st.container(key="card-skills"):
        st.html('<p class="section-title">Skills *</p>'
                '<p class="writer-help">Add a row for each skill. Click the + under the table to add one.</p>')
        draft_skills = [{"Skill": s["name"], "Type": s["type"], "Required level": s["required_level"], "Min years": None}
                        for s in draft.get("skills", [])]
        skills_table = st.data_editor(
            pd.DataFrame(draft_skills, columns=["Skill", "Type", "Required level", "Min years"]),
            num_rows="dynamic",
            hide_index=True,
            width="stretch",
            key=f"skills_{form}",
            column_config={
                "Skill": st.column_config.TextColumn(required=True),
                "Type": st.column_config.SelectboxColumn(options=SKILL_TYPES, default="Must-have"),
                "Required level": st.column_config.NumberColumn(min_value=1, max_value=5, step=1, default=3),
                "Min years": st.column_config.NumberColumn(min_value=0, max_value=30, step=1),
            },
        )

    # Turn the skills table into a plain list. Empty rows are skipped
    skills = []
    for _, row in skills_table.iterrows():
        if isinstance(row["Skill"], str) and row["Skill"].strip():
            skills.append({
                "name": row["Skill"].strip(),
                "type": row["Type"] if isinstance(row["Type"], str) else "",
                "required_level": int(row["Required level"]) if pd.notna(row["Required level"]) else 3,
                "min_years": int(row["Min years"]) if pd.notna(row["Min years"]) else None,
            })

    if st.button("Save job", type="primary", icon=":material/save:"):
        problem = check_new_job(title, description, level, work_type, skills)
        if problem:
            st.error(problem, icon=":material/error:")
        else:
            save_job(title, description, level, min_experience, location, work_type,
                     manager_names.get(manager), skills, user["email"])
            st.session_state.job_saved = f"Saved: {title.strip()}"
            # A bigger number = new keys = an empty form for the next job. The AI draft is used up
            st.session_state.job_draft = None
            st.session_state.job_form += 1
            st.rerun()
