# Score test: upload a job post and a CV, then see Agent 1's full result.
# The Score button sends the files to my FastAPI backend, which runs Agent 1.
from html import escape

import pandas as pd
import streamlit as st

import api_client
from components import card_title, chip, icon, icon_list, level_dots, load_page_css, page_header, part_bar, pill, score_gauge
from levels import LEVEL_WEIGHTS

load_page_css(__file__)
page_header("Score test", "Try Agent 1 on one job post and one CV, in 3 steps.", section="Tools")

# Show a clear warning at the top if the backend is off
if not api_client.is_running():
    st.warning(f"The backend is not running, so scoring won't work. "
               f"Start it in a second terminal: `{api_client.START_COMMAND}`", icon=":material/cloud_off:")

# ---------- Step 1 and 2: the inputs ----------
left, right = st.columns(2, gap="medium")

with left:
    with st.container(key="card-job"):
        st.html('<p class="step"><span>1</span>The job</p>')
        job_file = st.file_uploader("Upload a job post", type=["md", "txt", "pdf", "docx"])
        job_text = st.text_area("Or paste the job post", height=120,
                                placeholder="We are hiring a Junior Python Developer...")
        level = st.segmented_control("Level", ["Junior", "Mid", "Senior", "Team Lead"], default="Junior")

with right:
    with st.container(key="card-cv"):
        st.html('<p class="step"><span>2</span>The skills and the CV</p>')
        # Starts empty: HR types the skills for this job
        start_skills = pd.DataFrame(columns=["Skill", "Type", "Required level"])
        # A table I can edit. num_rows="dynamic" lets me add and delete rows
        skills_table = st.data_editor(
            start_skills,
            num_rows="dynamic",
            hide_index=True,
            width="stretch",
            column_config={
                "Type": st.column_config.SelectboxColumn(options=["Must-have", "Nice-to-have"]),
                "Required level": st.column_config.NumberColumn(min_value=1, max_value=5, step=1),
            },
        )
        cv_file = st.file_uploader("Upload a CV", type=["pdf", "docx"])

# Turn the table into a plain list. Rows with no skill name are skipped
skills = []
for _, row in skills_table.iterrows():
    if isinstance(row["Skill"], str) and row["Skill"].strip():
        skills.append({
            "skill": row["Skill"].strip(),
            "type": row["Type"] if isinstance(row["Type"], str) else "Must-have",
            "required_level": int(row["Required level"]) if pd.notna(row["Required level"]) else 1,
        })

# ---------- The Score button: the only place that calls the AI ----------
if st.button("Score this CV", type="primary", icon=":material/auto_awesome:", width="stretch"):
    if cv_file is None:
        st.error("Please upload a CV first.")
    elif job_file is None and not job_text.strip():
        st.error("Please upload or paste a job post.")
    elif not skills:
        st.error("Please add at least one skill.")
    elif level is None:
        st.error("Please pick a level.")
    else:
        with st.spinner("Agent 1 is reading the CV. This takes about 10 to 30 seconds..."):
            try:
                result = api_client.score_cv(level, skills, cv_file, job_text, job_file)
                # Keep the result, so it stays when the page reruns
                st.session_state.score_result = result
                st.session_state.score_info = {"cv": cv_file.name, "level": level, "skills": skills}
            except api_client.ApiError as error:
                st.session_state.score_result = None
                st.error(str(error), icon=":material/error:")

result = st.session_state.get("score_result")
if not result:
    st.html(f'<div class="empty-state">{icon("description", "empty-icon")}<br>'
            'Upload a CV and click <b>Score this CV</b> to see the result here.</div>')
    st.stop()

# The result belongs to the level and skills I scored with, not to what is in the boxes now
info = st.session_state.score_info
weights = LEVEL_WEIGHTS[info["level"]]

# ---------- Step 3: the result ----------
st.html(f'<p class="step result-step"><span>3</span>The result '
        f'<small>{escape(info["cv"])} · {info["level"]} · {result["model"]} · {result["seconds"]} seconds</small></p>')

# Trick lines first, so HR can't miss them
if result["trick_lines"]:
    found = ", ".join(f'"{escape(line)}"' for line in result["trick_lines"])
    st.html(f"""
        <div class="trick-alert">
            <b>{icon('gpp_maybe')} Trick lines found in this CV</b>
            <p>The CV has hidden orders for the AI: {found}. The AI was told to ignore them.</p>
        </div>
    """)

top_left, top_right = st.columns([1, 2], gap="medium")

with top_left:
    with st.container(key="card-total"):
        st.html('<p class="section-title">Total score</p>')
        st.html(score_gauge(result["total_score"]))
        st.html(f'<p class="total-note">for a <b>{info["level"]}</b> job</p>')

with top_right:
    with st.container(key="card-parts"):
        st.html('<p class="section-title">Part scores (0 to 5)</p>')
        parts = {
            "Skills": result["skills"],
            "Experience": result["experience"],
            "Projects": result["projects"],
            "Education": result["education"],
            "Leadership": result["leadership"],
            "Other": result["other"],
        }
        st.html("".join(part_bar(name, score, weights[name]) for name, score in parts.items()))

# ---------- Skill table ----------
# Python compares the found level with the required level
with st.container(key="card-skills"):
    st.html('<p class="section-title">Skill by skill</p>')
    required = {s["skill"].lower(): s for s in info["skills"]}
    rows = ""
    for s in result["skill_scores"]:
        need = required.get(s["skill"].lower())
        need_level = need["required_level"] if need else 0
        skill_type = need["type"] if need else "—"

        if s["level"] >= need_level:
            check = pill("Meets", "green")
        elif skill_type == "Must-have":
            check = pill("Must-have is low", "red")
        else:
            check = pill("Below", "amber")

        rows += f"""
            <tr>
                <td><b>{escape(s['skill'])}</b><br><small>{skill_type}</small></td>
                <td>{level_dots(s['level'], need_level)} <span class="lvl">{s['level']}/5</span></td>
                <td>{need_level}/5</td>
                <td>{check}</td>
                <td class="proof">“{escape(s['proof'])}”</td>
            </tr>
        """
    st.html(f"""
        <table class="skill-table">
            <thead><tr><th>Skill</th><th>Found</th><th>Needed</th><th>Check</th><th>Proof from the CV</th></tr></thead>
            <tbody>{rows}</tbody>
        </table>
        <p class="hint">The orange ring shows the needed level. A low must-have is only a warning for HR, never a reject.</p>
    """)

# ---------- Strengths, weak points, missing skills ----------
col1, col2, col3 = st.columns(3, gap="medium")
with col1:
    with st.container(key="card-strengths"):
        st.html(card_title("thumb_up", "Strengths", "mi-green"))
        st.html(icon_list([escape(item) for item in result["strengths"]], "check"))
with col2:
    with st.container(key="card-weak"):
        st.html(card_title("search", "Weak points", "mi-amber"))
        st.html(icon_list([escape(item) for item in result["weak_points"]], "remove"))
with col3:
    with st.container(key="card-missing"):
        st.html(card_title("block", "Missing skills", "mi-red"))
        if result["missing_skills"]:
            st.html("".join(chip(escape(skill), "missing") for skill in result["missing_skills"]))
        else:
            st.html('<p class="hint">Nothing is missing.</p>')

# ---------- Proof lines, checked against the CV text ----------
with st.container(key="card-proof"):
    st.html('<p class="section-title">Proof lines copied from the CV</p>')
    for check in result["proof_checks"]:
        if check["found"]:
            badge = f'<span>{icon("check_circle")} found in the CV</span>'
            css_class = "proof-line"
        else:
            badge = f'<span class="not-found">{icon("error")} not found in the CV</span>'
            css_class = "proof-line proof-missing"
        st.html(f'<blockquote class="{css_class}">{escape(check["line"])} {badge}</blockquote>')
