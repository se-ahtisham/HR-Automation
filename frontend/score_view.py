# Shows Agent 1's full result (Upload & score CVs, Candidates), and the "Send score to candidate" button
from html import escape

import streamlit as st

from app.core.score_email import send_score_email, write_score_email
from components import FRONTEND, add_css, card_title, chip, icon, icon_list, level_dots, part_bar, pill, score_gauge
from levels import LEVEL_WEIGHTS


# result = the dictionary from score_with_checks.
# level and skills = what the CV was scored with. skills: [{"skill", "type", "required_level"}]
def show_score_result(result, level, skills, title_note=""):
    add_css(FRONTEND / "score_view.css")
    weights = LEVEL_WEIGHTS[level]

    # A saved score has no time, so the seconds only show right after scoring
    seconds = f' · {result["seconds"]} seconds' if result["seconds"] else ""
    st.html(f'<p class="step result-step"><span>3</span>The result <small>{escape(title_note)} · {level} · '
            f'{result["model"]}{seconds}</small></p>')

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
            st.html(f'<p class="total-note">for a <b>{level}</b> job</p>')
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

    # ---------- Skill table: Python compares the found level with the required level ----------
    with st.container(key="card-skills"):
        st.html('<p class="section-title">Skill by skill</p>')
        required = {s["skill"].lower(): s for s in skills}
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
                badge = f'<span class="found">{icon("check_circle")} found in the CV</span>'
                css_class = "proof-line"
            else:
                badge = f'<span class="not-found">{icon("error")} not found in the CV</span>'
                css_class = "proof-line proof-missing"
            st.html(f'<div class="{css_class}"><span class="proof-text">{escape(check["line"])}</span>{badge}</div>')


# The "Send score to candidate" button: sends the CV Match Score email once.
# Used on the Upload & score CVs page and on the candidate's profile
def send_score_button(candidate_id, hr_email):
    if st.button("Send score to candidate", icon=":material/mail:", width="stretch", key=f"send_score_{candidate_id}"):
        status = send_score_email(candidate_id, hr_email)
        messages = {
            "Sent": "The CV Match Score email was sent.",
            "MOCK": "MOCK: no email keys in .env, so the email was saved but not really sent.",
            "Failed": "The email could not be sent. Check SMTP_EMAIL and SMTP_APP_PASSWORD in .env.",
            "Already sent": "This candidate already got their score email.",
            "No email": "No email address was found in this CV.",
        }
        st.toast(messages[status], icon=":material/mail:")


# HR can see the designed email before (or after) sending it
def show_email_preview(candidate_id, hidden=False):
    # Blind Mode: the email says the candidate's name, so it isn't shown
    if hidden:
        st.caption("The email preview is hidden in Blind Mode (it shows the name).")
        return
    with st.expander("Preview the score email", icon=":material/visibility:"):
        to_email, subject, html = write_score_email(candidate_id)
        st.caption(f"To: {to_email or 'no email found'} · Subject: {subject}")
        st.html(html)
