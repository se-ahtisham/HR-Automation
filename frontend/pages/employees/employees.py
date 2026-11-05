# Employees: add, see, edit and turn off people. Interviewers get free times.
import pandas as pd
import streamlit as st

from components import avatar, empty_state, load_page_css, page_header, pill

load_page_css(__file__)
page_header("Employees", "Interviewers, hiring managers, HR and admins. People are turned off, never deleted.", section="Manage")

# Real data comes from the backend in the next step. Until then the list is empty
EMPLOYEES = []

list_tab, edit_tab = st.tabs(["All employees", "Add or edit"])

# ---------- Tab 1: the list ----------
with list_tab:
    if not EMPLOYEES:
        st.html(empty_state("badge", "No employees yet",
                            "Open the Add or edit tab to add interviewers and other staff, with their free times."))
    rows = ""
    for e in EMPLOYEES:
        interview = pill("Can interview", "violet") if e["can_interview"] else ""
        active = pill("Active", "green") if e["active"] else pill("Turned off", "gray")
        rows += f"""
            <tr class="{'' if e['active'] else 'off'}">
                <td><div class="who">{avatar(e['name'], 'sm')}<b>{e['name']}</b></div></td>
                <td>{e['role']}</td>
                <td>{e['time_zone']}</td>
                <td>{interview}</td>
                <td>{active}</td>
            </tr>
        """
    if EMPLOYEES:
        with st.container(key="card-people"):
            st.html(f"""
                <table class="people">
                    <thead><tr><th>Name</th><th>Role</th><th>Time zone</th><th>Interviews</th><th>Status</th></tr></thead>
                    <tbody>{rows}</tbody>
                </table>
            """)

# ---------- Tab 2: add or edit one person ----------
with edit_tab:
    names = ["New employee"] + [e["name"] for e in EMPLOYEES]
    picked = st.selectbox("Person", names)
    person = next((e for e in EMPLOYEES if e["name"] == picked), None)

    with st.container(key="card-form"):
        col1, col2 = st.columns(2)
        col1.text_input("Full name", value=person["name"] if person else "")
        col2.text_input("Email", placeholder="name@company.com")
        col1, col2 = st.columns(2)
        roles = ["Admin", "HR", "Hiring Manager", "Interviewer"]
        col1.selectbox("Role", roles, index=roles.index(person["role"]) if person else 3)
        zones = ["Asia/Karachi", "Asia/Dubai", "Europe/London", "America/New_York"]
        col2.selectbox("Time zone", zones, index=zones.index(person["time_zone"]) if person else 0)
        can_interview = st.toggle("Can this person conduct interviews?",
                                  value=person["can_interview"] if person else False)

    # Free times show only when the person can interview
    if can_interview:
        with st.container(key="card-times"):
            st.html('<p class="section-title">Free times every week</p>')
            st.data_editor(
                pd.DataFrame(columns=["day", "start", "end"]),
                num_rows="dynamic",
                hide_index=True,
                width="stretch",
                column_config={
                    "day": st.column_config.SelectboxColumn(
                        "Day", options=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]),
                    "start": st.column_config.TextColumn("Start"),
                    "end": st.column_config.TextColumn("End"),
                },
            )
            st.html('<p class="section-title" style="margin-top:0.8rem">One-off busy times</p>')
            col1, col2, col3 = st.columns(3)
            col1.date_input("Date")
            col2.time_input("From")
            col3.time_input("To")

    col1, col2, _ = st.columns([1, 1, 3])
    if col1.button("Save", type="primary", icon=":material/save:", width="stretch"):
        st.toast("MOCK: not saved yet. Every change will go to the audit log.", icon=":material/save:")
    if person and person["active"]:
        col2.button("Turn off", icon=":material/person_off:", width="stretch")
