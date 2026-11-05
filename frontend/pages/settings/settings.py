# Settings: the scheduling rules, privacy and switches. Saved in the database later.
from datetime import time

import streamlit as st

from components import card_title, load_page_css, page_header

load_page_css(__file__)
page_header("Settings", "Rules for scheduling, calls, emails and data. Every change goes to the audit log.", section="Manage")

left, right = st.columns(2, gap="medium")

with left:
    with st.container(key="card-interview"):
        st.html(card_title("calendar_month", "Interviews"))
        col1, col2 = st.columns(2)
        col1.number_input("Length (min)", 15, 180, 45, step=15)
        col2.number_input("Break between (min)", 0, 60, 15, step=5)
        col1, col2 = st.columns(2)
        col1.time_input("Work starts", value=time(9, 0))
        col2.time_input("Work ends", value=time(17, 0))
        st.multiselect("Work days", ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
                       default=["Mon", "Tue", "Wed", "Thu", "Fri"])
        st.selectbox("Default time zone", ["Asia/Karachi", "Asia/Dubai", "Europe/London"])

    with st.container(key="card-booking"):
        st.html(card_title("event_available", "Booking"))
        col1, col2 = st.columns(2)
        col1.number_input("Days ahead", 1, 60, 14)
        col2.number_input("Notice (hours)", 0, 72, 24)
        col1, col2 = st.columns(2)
        col1.number_input("Times to offer", 1, 10, 3)
        col2.number_input("Max interviews per day", 1, 20, 4)

with right:
    with st.container(key="card-calls"):
        st.html(card_title("call", "Calls"))
        st.number_input("Call tries before giving up", 1, 5, 3)
        st.toggle("Use pretend calls (MOCK)", value=True, help="USE_MOCK_CALLS. Turn off only for my own test phone.")

    with st.container(key="card-emails"):
        st.html(card_title("mail", "Emails"))
        st.toggle("Send the CV Match Score email automatically", value=True)
        st.caption("It is sent only once per candidate per job, and never says \"rejected\".")

    with st.container(key="card-privacy"):
        st.html(card_title("lock", "Privacy", "mi-green"))
        st.slider("Keep candidate data for (days)", 30, 365, 90, step=30)
        st.toggle("Blind Mode on by default", value=True)

if st.button("Save settings", type="primary", icon=":material/save:"):
    st.toast("MOCK: settings are not saved yet.", icon=":material/save:")
