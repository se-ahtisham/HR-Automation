# Interviews: Agent 3 finds free times, writes the invite, and HR confirms (HR stop #3)
import streamlit as st

from components import empty_state, icon, load_page_css, page_header, status_badge

load_page_css(__file__)
page_header("Interviews", "Agent 3 finds free times. Nothing is sent before you confirm.", section="Hiring")

# Real data comes from the backend later (Agent 3, Day 7). Until then every list is empty
READY_CANDIDATES = []   # candidates approved for an interview
SLOTS = []              # free times that work for both sides
INTERVIEWS = []         # interviews that are proposed or booked

find_tab, invite_tab, all_tab = st.tabs(["Find a time", "Invite email", "All interviews"])

# ---------- Tab 1: free times ----------
with find_tab:
    if not READY_CANDIDATES:
        st.html(empty_state("event_available", "No one is ready for an interview yet",
                            "Approve a candidate after the screening call, then find a time here."))
    else:
        st.selectbox("Candidate", [c["name"] for c in READY_CANDIDATES])
        st.html('<p class="section-title">Free times for both sides</p>')
        columns = st.columns(max(len(SLOTS), 1))
        for number, slot in enumerate(SLOTS):
            with columns[number]:
                with st.container(key=f"card-slot-{number}"):
                    st.html(f"""
                        <div class="slot">
                            <p class="slot-day">{slot['day']}</p>
                            <p class="slot-time">{slot['time']}</p>
                            <p class="slot-zone">{icon('public')} {slot['zone']}</p>
                            <p class="slot-person">{icon('person')} {slot['interviewer']}</p>
                        </div>
                    """)
                    st.button("Pick this time", key=f"pick_{number}", width="stretch")
        st.caption("Times come from each interviewer's free hours, minus their busy times, inside the Settings rules.")

# ---------- Tab 2: the invite email ----------
with invite_tab:
    st.html(empty_state("mail", "No invite to write yet",
                        "Pick a free time first. The invite email is drafted here, and it is sent only after you confirm."))

# ---------- Tab 3: all interviews ----------
with all_tab:
    if not INTERVIEWS:
        st.html(empty_state("calendar_month", "No interviews yet", "Booked and proposed interviews show here."))
    for number, interview in enumerate(INTERVIEWS):
        with st.container(key=f"card-interview-{number}"):
            info_col, button_col = st.columns([3, 1.4], vertical_alignment="center")
            info_col.html(f"""
                <p class="iv-name">{interview['candidate']} <small>· {interview['job']}</small></p>
                <p class="iv-meta">{icon('calendar_today')} {interview['when']} &nbsp;·&nbsp; {icon('person')} {interview['interviewer']}</p>
                {status_badge(interview['status'])}
            """)
            with button_col:
                col1, col2 = st.columns(2)
                col1.button("Move", key=f"move_{number}", icon=":material/schedule:", width="stretch")
                col2.button("Cancel", key=f"cancel_{number}", icon=":material/event_busy:", width="stretch")
