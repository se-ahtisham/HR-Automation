# Settings: the rules Agent 3 (the scheduler), the calls and the privacy clean-up use. Every change goes to the audit log
from html import escape

import streamlit as st
from pydantic import ValidationError

from app.core.audit import list_history
from app.core.settings import get_settings, save_settings
from components import card_title, load_page_css, page_header

load_page_css(__file__)
page_header("Settings", "Rules for scheduling, calls and data. Every change goes to the audit log.", section="Manage")

user = st.session_state.user
now = get_settings()
TIME_ZONES = ["Asia/Karachi", "Asia/Dubai", "Europe/London", "America/New_York"]
MEETING_TYPES = ["Online", "In the office"]

# A form: nothing is saved until "Save settings" is clicked
with st.form("settings_form", border=False):
    left, right = st.columns(2, gap="medium")
    with left:
        with st.container(key="card-interview"):
            st.html(card_title("calendar_month", "Interviews"))
            col1, col2 = st.columns(2)
            interview_minutes = col1.number_input("Length (minutes)", 15, 240, now["interview_minutes"], step=15)
            break_minutes = col2.number_input("Break between (minutes)", 0, 120, now["break_minutes"], step=5)
            col1, col2 = st.columns(2)
            timezone = col1.selectbox("Time zone", TIME_ZONES, index=TIME_ZONES.index(now["timezone"]))
            meeting_type = col2.selectbox("How", MEETING_TYPES, index=MEETING_TYPES.index(now["meeting_type"]))

        with st.container(key="card-booking"):
            st.html(card_title("event_available", "Booking"))
            col1, col2 = st.columns(2)
            booking_days = col1.number_input("Book up to (days ahead)", 1, 60, now["booking_days"])
            notice_hours = col2.number_input("Notice (hours)", 0, 168, now["notice_hours"])
            col1, col2 = st.columns(2)
            time_choices = col1.number_input("Times to offer", 1, 10, now["time_choices"])
            max_per_day = col2.number_input("Max interviews a day (per interviewer)", 1, 20, now["max_per_day"])

    with right:
        with st.container(key="card-privacy"):
            st.html(card_title("lock", "Privacy", "mi-green"))
            keep_data_days = st.slider("Keep candidate data for (days)", 30, 365, now["keep_data_days"], step=5,
                                       help="Older candidates and their CV files are deleted once per login.")

    saved = st.form_submit_button("Save settings", type="primary", icon=":material/save:")

if saved:
    # The Settings model checks every value before it is saved
    values = {
        "interview_minutes": interview_minutes, "break_minutes": break_minutes, "timezone": timezone,
        "meeting_type": meeting_type, "booking_days": booking_days, "notice_hours": notice_hours,
        "time_choices": time_choices, "max_per_day": max_per_day, "keep_data_days": keep_data_days,
    }
    try:
        changes = save_settings(values, user["email"])
        st.toast(f"Saved {len(changes)} changes." if changes else "Nothing changed.", icon=":material/check_circle:")
    except ValidationError as error:
        st.error(error.errors()[0]["msg"], icon=":material/error:")

# Write it down: the last changes, from the audit log
with st.container(key="card-history"):
    st.html(card_title("history", "Recent changes"))
    history = list_history("settings", 1, limit=5)
    if not history:
        st.caption("No changes yet. The defaults are used.")
    for event in history:
        st.html(f'<p class="change"><span>{event["timestamp"][:16]}</span> <b>{escape(event["actor"])}</b>: '
                f'{escape(event["details"])}</p>')
