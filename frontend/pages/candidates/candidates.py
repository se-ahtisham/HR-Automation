# Candidates: every candidate with their score. HR approves for calling (HR stop #1), then the script agent calls them
import json
import os
from html import escape

import streamlit as st

from app.agents.script_agent.agent import call_candidate, get_call_result
from app.agents.script_agent.save_call import save_call_result, save_call_started
from app.core.audit import list_history
from app.core.candidates import approve_for_calling, decline, delete_candidate, fix_candidate, list_candidates, saved_score
from app.core.cv_scoring import job_skills
from app.core.jobs import list_jobs
from components import FRONTEND, add_css, avatar, card_title, empty_state, icon_list, load_page_css, page_header, status_badge
from score_view import send_score_button, show_email_preview, show_score_result

load_page_css(__file__)
add_css(FRONTEND / "score_view.css")

user = st.session_state.user
candidates = list_candidates()

if "picked_candidate" not in st.session_state:
    st.session_state.picked_candidate = None


# ======================= One candidate's profile =======================
# The picked candidate may be gone (deleted), so None goes back to the list
c = next((p for p in candidates if p["id"] == st.session_state.picked_candidate), None)
if c is None:
    st.session_state.picked_candidate = None

if c is not None:

    back_col, _, fix_col, delete_col = st.columns([1.5, 2, 1, 1], vertical_alignment="center")
    if back_col.button("Back to all candidates", icon=":material/arrow_back:", type="tertiary"):
        st.session_state.picked_candidate = None
        st.rerun()

    # Fix: the CV reader can get a name, email or phone wrong, so HR can correct them
    with fix_col.popover("Fix details", icon=":material/edit:", width="stretch"):
        new_name = st.text_input("Name", value=c["name"], key=f"fix_name_{c['id']}")
        new_email = st.text_input("Email", value=c["email"] or "", key=f"fix_email_{c['id']}")
        new_phone = st.text_input("Phone (with country code)", value=c["phone"] or "", key=f"fix_phone_{c['id']}")
        if st.button("Save", type="primary", key=f"fix_save_{c['id']}", width="stretch"):
            problem = fix_candidate(c["id"], new_name, new_email, new_phone, user["email"])
            if problem:
                st.error(problem, icon=":material/error:")
            else:
                st.rerun()

    # Delete for good: the popover asks again, so one wrong click doesn't delete anyone
    with delete_col.popover("Delete", icon=":material/delete:", width="stretch"):
        st.write(f"Delete **{c['name']}**, their score, their call and their CV file? This can't be undone.")
        if st.button("Yes, delete", type="primary", icon=":material/delete_forever:", width="stretch"):
            delete_candidate(c["id"], user["email"])
            st.session_state.picked_candidate = None
            st.rerun()

    with st.container(key="card-head"):
        st.html(f"""
            <div class="head">
                {avatar(c['name'], 'lg')}
                <div>
                    <h2 class="detail-name">{escape(c['name'])}</h2>
                    <p class="detail-meta">{escape(c['job_title'])} · {c['level']} · Score {c['total_score'] or '-'}/100</p>
                    {status_badge(c['current_status'])}
                    <p class="contact">{escape(c['email'] or 'No email')} &nbsp;·&nbsp; {escape(c['phone'] or 'No phone')}</p>
                </div>
            </div>
        """)

    # History: every step for this candidate, who did it and when (from the audit log)
    with st.expander("History", icon=":material/history:"):
        for event in list_history("candidate", c["id"]):
            details = f" · {escape(event['details'])}" if event["details"] else ""
            st.html(f'<p class="history-line"><span>{event["timestamp"][:16]}</span> <b>{escape(event["actor"])}</b> '
                    f'{escape(event["action"])}{details}</p>')

    status = c["current_status"]

    # ---------- HR stop #1: approve for calling, or decline ----------
    if status == "Scored (HR Review)":
        with st.container(key="card-decision"):
            st.html('<p class="section-title">Your decision</p>')
            if st.button("Approved for calling", type="primary", icon=":material/check:", width="stretch"):
                approve_for_calling(c["id"], user["email"])
                st.rerun()
            reason = st.text_input("Reason to decline", placeholder="Why not this candidate?")
            if st.button("Decline", icon=":material/close:", width="stretch"):
                if reason.strip():
                    decline(c["id"], reason.strip(), user["email"])
                    st.rerun()
                else:
                    st.error("Please write a reason first.")

    # ---------- The script agent phones the candidate ----------
    if status == "Approved for Calling":
        with st.container(key="card-decision"):
            st.html(card_title("call", "Call the candidate") +
                    '<p class="hint">The script agent asks the 4 questions, then gives HR a summary. Only call test numbers.</p>')
            if not c["phone"]:
                st.warning("No phone number was found in this CV.", icon=":material/phone_disabled:")
            elif not os.environ.get("ELEVENLABS_PHONE_NUMBER_ID"):
                st.info("Add ELEVENLABS_PHONE_NUMBER_ID to .env first (my Twilio number in ElevenLabs).", icon=":material/info:")
            elif st.button(f"Call {c['phone']}", type="primary", icon=":material/call:", width="stretch"):
                conversation_id = call_candidate(c["phone"], c["name"], c["job_title"])
                save_call_started(c["id"], conversation_id, user["email"])
                st.rerun()

    # ---------- The call is on, or just ended ----------
    if status == "Screening Pending":
        with st.container(key="card-decision"):
            st.html(card_title("phone_in_talk", "The call is on") + '<p class="hint">When the call ends, get the answers and the summary.</p>')
            if st.button("Get the call result", type="primary", icon=":material/download:", width="stretch"):
                result = get_call_result(c["conversation_id"])
                if result is None:
                    st.info("The call isn't finished yet. Try again in a few seconds.", icon=":material/hourglass_top:")
                else:
                    save_call_result(c["id"], c["conversation_id"], result, user["email"])
                    st.rerun()

    # ---------- What the candidate said, saved in the database ----------
    if c["call_status"] == "Done":
        answers = json.loads(c["answers"] or "{}")
        said = [
            f"<b>Consent:</b> {escape(c['consent_status'] or '-')}",
            f"<b>Available for interview:</b> {escape(c['candidate_availability'] or 'Not given')}",
            f"<b>Previous job:</b> {escape(answers.get('previous_job') or 'Not given')}",
            f"<b>Why they want to shift:</b> {escape(answers.get('reason_for_shift') or 'Not given')}",
        ]
        with st.container(key="card-call-result"):
            st.html(card_title("record_voice_over", "What the candidate said", "mi-green") + icon_list(said, "check") +
                    card_title("summarize", "Summary of the call") + f"<p>{escape(c['summary'] or '')}</p>")

    if c["total_score"] is None:
        st.error("This CV could not be read or scored. A human must check it.", icon=":material/error:")
    else:
        send_score_button(c["id"], user["email"])
        show_email_preview(c["id"])
        job = next(j for j in list_jobs() if j["id"] == c["job_id"])
        show_score_result(saved_score(c), c["level"], job_skills(job), c["name"])
    st.stop()


# ======================= All candidates =======================
page_header("Candidates", "Best score first. Approved candidates show first, ready for the script agent to call.", section="Hiring")

if not candidates:
    st.html(empty_state("group", "No candidates yet", "Upload and score CVs. Each scored CV shows here."))
    st.stop()

# One simple filter: the status. It starts on the candidates HR approved for calling
STATUSES = ["Approved for Calling", "Screening Pending", "Screening Completed (HR Review)",
            "Scored (HR Review)", "Needs Manual Review", "Closed"]
status = st.selectbox("Status", STATUSES, format_func=lambda s: f"{s} · {sum(c['current_status'] == s for c in candidates)}")
people = [c for c in candidates if c["current_status"] == status]
if not people:
    st.html('<div class="empty">No candidates with this status.</div>')

columns = st.columns(3)
for number, c in enumerate(people):
    with columns[number % 3]:
        with st.container(key=f"card-person-{c['id']}"):
            score = f'{c["total_score"]}<small>/100</small>' if c["total_score"] is not None else "No score"
            st.html(f"""
                <div class="person-top">{avatar(c['name'], 'md')}<span class="score-pill">{score}</span></div>
                <p class="person-name">{escape(c['name'])}</p>
                <p class="person-job">{escape(c['job_title'])}</p>
                {status_badge(c['current_status'])}
            """)
            if st.button("Open", key=f"open_{c['id']}", type="primary", width="stretch"):
                st.session_state.picked_candidate = c["id"]
                st.rerun()
