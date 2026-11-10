# Interviews: Agent 3 finds free times and writes the invite. Nothing is sent before HR says yes (HR stop #3)
import json
from datetime import datetime
from html import escape

import streamlit as st

from app.agents.scheduling.flow import plan_interview
from app.agents.scheduling.free_times import find_free_slots
from app.agents.scheduling.prompts import CANCELLED_EMAIL, MOVED_EMAIL
from app.agents.scheduling.save_interview import cancel_interview, list_interviews, move_interview, send_invite
from app.core.candidates import list_candidates
from app.core.settings import get_settings
from components import empty_state, icon, load_page_css, page_header, pill

load_page_css(__file__)
page_header("Interviews", "Agent 3 finds free times and writes the invite. Nothing is sent before you say yes.", section="Hiring")

user = st.session_state.user
ready = [c for c in list_candidates() if c["current_status"] == "Approved for Interview"]
interviews = list_interviews()
proposals = [i for i in interviews if i["status"] == "Proposed"]


# "2026-11-10 14:00" → "Tuesday 10 Nov, 14:00"
def nice_time(value):
    return datetime.fromisoformat(value).strftime("%A %d %b, %H:%M")


find_tab, invite_tab, all_tab = st.tabs([f"Find a time · {len(ready)}", f"Invite email · {len(proposals)}", "All interviews"])

# ---------- Tab 1: Agent 3 finds times for candidates HR approved after the call ----------
with find_tab:
    if not ready:
        st.html(empty_state("event_available", "No one is waiting for a time",
                            "After a call, approve a candidate for an interview on their profile. They show here."))
    for c in ready:
        with st.container(key=f"card-interview-{c['id']}"):
            info_col, button_col = st.columns([3, 1.2], vertical_alignment="center")
            info_col.html(f"""
                <p class="iv-name">{escape(c['name'])} <small>· {escape(c['job_title'])}</small></p>
                <p class="iv-meta">{icon('schedule')} Said on the call: {escape(c['candidate_availability'] or 'no time given')}</p>
            """)
            if button_col.button("Find times & write invite", key=f"plan_{c['id']}", type="primary", icon=":material/auto_awesome:",
                                 width="stretch"):
                with st.spinner("Agent 3 is reading the candidate's times and finding free interviewers..."):
                    result = plan_interview(c["id"], user["email"])
                if result == "Proposed":
                    st.toast("Times found and invite written. Check it in the Invite email tab.", icon=":material/event_available:")
                else:
                    st.toast("No time works for both. It's on the HR to-do list.", icon=":material/warning:")
                st.rerun()

# ---------- Tab 2: HR picks a time, reads the email, and says yes (HR stop #3) ----------
with invite_tab:
    if not proposals:
        st.html(empty_state("mail", "No invites to check", "Find a time for a candidate first, in the first tab."))
    for interview in proposals:
        slots = json.loads(interview["proposed_slots"])
        draft = json.loads(interview["email_draft"])
        failed = interview["send_status"] == "Failed"
        with st.container(key=f"card-email-{interview['id']}"):
            st.html(f'<p class="iv-name">{escape(interview["candidate_name"])} <small>· {escape(interview["job_title"])} · '
                    f'{escape(interview["candidate_email"] or "no email")}</small></p>')
            if failed:
                st.warning("Sending failed last time (internet or Gmail problem). Check the details, then press Resend.",
                           icon=":material/error:")

            # The times that work for both. HR picks one
            picked = st.radio("Interview time", range(len(slots)), key=f"slot_{interview['id']}",
                              format_func=lambda n: f"{nice_time(slots[n]['start'])} · {slots[n]['interviewer']}")
            st.caption(f"Time zone: {interview['timezone']} · {interview['meeting_details']}")

            # The email the AI wrote. HR can change anything before sending
            subject = st.text_input("Subject", value=draft["subject"], key=f"subject_{interview['id']}")
            body = st.text_area("Email", value=draft["body"], height=230, key=f"body_{interview['id']}")
            if picked != 0:
                st.info(f"The email was written for {nice_time(slots[0]['start'])}. Change the time in the text to match your pick.",
                        icon=":material/edit:")

            label = "Resend email" if failed else "Approve & send"
            if st.button(label, key=f"send_{interview['id']}", type="primary", icon=":material/send:"):
                if not body.strip():
                    st.error("Please write the email first.", icon=":material/error:")
                else:
                    status = send_invite(interview["id"], slots[picked], subject, body, user["email"])
                    messages = {
                        "Sent": "The invite was sent. The interview is booked.",
                        "MOCK": "MOCK: no email keys in .env, so the invite was saved but not really sent. The interview is booked.",
                        "Failed": "Sending failed. Press Resend to try again.",
                        "Already sent": "This invite was already sent.",
                    }
                    st.toast(messages[status], icon=":material/mail:")
                    st.rerun()

# ---------- Tab 3: every interview ----------
with all_tab:
    if not interviews:
        st.html(empty_state("event", "No interviews yet", "Booked and proposed interviews show here."))
    for interview in interviews:
        with st.container(key=f"card-all-{interview['id']}"):
            when = nice_time(interview["confirmed_slot"]) if interview["confirmed_slot"] else "Time not picked yet"
            colors = {"Sent": "green", "MOCK": "green", "Failed": "red"}
            info_col, move_col, cancel_col = st.columns([4, 1, 1], vertical_alignment="center")
            info_col.html(f"""
                <p class="iv-name">{escape(interview['candidate_name'])} <small>· {escape(interview['job_title'])}</small></p>
                <p class="iv-meta">{icon('event')} {when} &nbsp; {icon('person')} {escape(interview['interviewer_name'] or '-')}
                   &nbsp; {pill(interview['status'], 'violet')} {pill('Email: ' + interview['send_status'], colors.get(interview['send_status'], 'gray'))}</p>
            """)
            if interview["status"] != "Scheduled":
                continue
            names = {"name": interview["candidate_name"], "job": interview["job_title"], "timezone": interview["timezone"]}

            # Move: pick a new free time, read the update email, send it. The time changes only if the email went out
            with move_col.popover("Move", icon=":material/edit_calendar:", width="stretch"):
                new_times = find_free_slots([], get_settings())
                if not new_times:
                    st.warning("No free time in the booking days. Add free times on Employees.", icon=":material/warning:")
                else:
                    picked = st.radio("New time", range(len(new_times)), key=f"move_slot_{interview['id']}",
                                      format_func=lambda n: f"{nice_time(new_times[n]['start'])} · {new_times[n]['interviewer']}")
                    text = MOVED_EMAIL.format(**names, when=nice_time(new_times[picked]["start"]))
                    # The key has the picked time, so the email text changes when HR picks another time
                    body = st.text_area("Email", value=text, height=200, key=f"move_body_{interview['id']}_{picked}")
                    if st.button("Send & move", type="primary", key=f"move_{interview['id']}", icon=":material/send:"):
                        status = move_interview(interview["id"], new_times[picked], f"Your interview has moved: {interview['job_title']}",
                                                body, user["email"])
                        st.toast("Sending failed. Nothing changed: try again." if status == "Failed" else f"Moved ({status}).",
                                 icon=":material/edit_calendar:")
                        st.rerun()

            # Cancel: a reason is needed, read the cancel email, send it. Cancelled only if the email went out
            with cancel_col.popover("Cancel", icon=":material/event_busy:", width="stretch"):
                reason = st.text_input("Reason (for the log)", key=f"cancel_reason_{interview['id']}",
                                       placeholder="The role was filled")
                body = st.text_area("Email", value=CANCELLED_EMAIL.format(**names, when=when), height=180,
                                    key=f"cancel_body_{interview['id']}")
                if st.button("Send & cancel", type="primary", key=f"cancel_{interview['id']}", icon=":material/send:"):
                    if not reason.strip():
                        st.error("Please write a reason first.", icon=":material/error:")
                    else:
                        status = cancel_interview(interview["id"], reason.strip(), f"Interview cancelled: {interview['job_title']}",
                                                  body, user["email"])
                        st.toast("Sending failed. Nothing changed: try again." if status == "Failed" else f"Cancelled ({status}).",
                                 icon=":material/event_busy:")
                        st.rerun()
