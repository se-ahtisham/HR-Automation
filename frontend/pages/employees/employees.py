# Employees: add, see, edit and turn off people. Interviewers get weekly free times and one-off busy times
from datetime import datetime, time
from html import escape

import pandas as pd
import streamlit as st

from app.core.employees import (DAYS, ROLES, TIME_ZONES, add_busy_time, check_employee, delete_busy_time, list_employees,
                                save_employee, set_active)
from components import avatar, empty_state, load_page_css, page_header, pill

load_page_css(__file__)
page_header("Employees", "Interviewers, hiring managers, HR and admins. People are turned off, never deleted.", section="Manage")

user = st.session_state.user
employees = list_employees()

# A number in the form keys. Making it bigger after saving gives an empty form for the next person
if "employee_form" not in st.session_state:
    st.session_state.employee_form = 0


# The form, used 2 times: empty to add a person, and filled in to edit one. person = {} means a new person
def employee_form(person):
    employee_id = person.get("id")
    # The keys have the person's id, so each person's form keeps its own values
    k = f"{employee_id or 'new'}_{st.session_state.employee_form}"

    col1, col2 = st.columns(2)
    name = col1.text_input("Full name *", value=person.get("name", ""), key=f"name_{k}")
    email = col2.text_input("Email *", value=person.get("email", ""), placeholder="name@company.com", key=f"email_{k}")
    col1, col2, col3 = st.columns(3)
    role = col1.selectbox("Role", ROLES, index=ROLES.index(person.get("role", "Interviewer")), key=f"role_{k}")
    team = col2.text_input("Team", value=person.get("team") or "", placeholder="Backend", key=f"team_{k}")
    timezone = col3.selectbox("Time zone", TIME_ZONES, index=TIME_ZONES.index(person.get("timezone", "Asia/Karachi")),
                              key=f"zone_{k}")
    can_interview = st.toggle("Can this person conduct interviews?", value=bool(person.get("can_interview")), key=f"interview_{k}")

    # Weekly free times show only when the person can interview. "09:00" text in the database, time boxes on the page
    free_times = []
    if can_interview:
        st.html('<p class="section-title">Free times every week</p>'
                '<p class="hint">Add a row for each free time. Click the + under the table to add one.</p>')
        saved = pd.DataFrame(
            [{"Day": t["day_of_week"], "From": time.fromisoformat(t["start_time"]), "To": time.fromisoformat(t["end_time"])}
             for t in person.get("free_times", [])],
            columns=["Day", "From", "To"],
        )
        table = st.data_editor(
            saved, num_rows="dynamic", hide_index=True, width="stretch", key=f"times_{k}",
            column_config={
                "Day": st.column_config.SelectboxColumn(options=DAYS, required=True),
                "From": st.column_config.TimeColumn(format="HH:mm", step=900, required=True),
                "To": st.column_config.TimeColumn(format="HH:mm", step=900, required=True),
            },
        )
        # Turn the table into plain rows. Rows that are not filled in are skipped
        for _, row in table.iterrows():
            if isinstance(row["Day"], str) and pd.notna(row["From"]) and pd.notna(row["To"]):
                free_times.append({"day_of_week": row["Day"], "start_time": row["From"].strftime("%H:%M"),
                                   "end_time": row["To"].strftime("%H:%M")})

    if st.button("Save", type="primary", icon=":material/save:", key=f"save_{k}"):
        problem = check_employee(employee_id, name, email, free_times)
        if problem:
            st.error(problem, icon=":material/error:")
        else:
            save_employee(employee_id, name, email, role, team, timezone, can_interview, free_times, user["email"])
            st.session_state.employee_form += 1
            st.toast(f"Saved: {name.strip()}", icon=":material/check_circle:")
            st.rerun()


# Edit one person in a pop-up window: the same form, plus turn off / on and busy times.
# The person is read fresh each time, so a new busy time shows at once.
# st.rerun(scope="fragment") redraws only the pop-up, so it stays open
@st.dialog("Edit employee", width="large")
def edit_employee(employee_id):
    person = next(e for e in list_employees() if e["id"] == employee_id)
    employee_form(person)

    # Turn off instead of delete, so old interviews still show who did them
    if person["is_active"]:
        if st.button("Turn off", icon=":material/person_off:"):
            set_active(person["id"], False, user["email"])
            st.rerun(scope="fragment")
    elif st.button("Turn on", icon=":material/person_add:"):
        set_active(person["id"], True, user["email"])
        st.rerun(scope="fragment")

    # One-off busy times: only for someone who can interview
    if person["can_interview"]:
        st.html('<p class="section-title">One-off busy times</p>'
                '<p class="hint">Leave, meetings, a day off. The scheduler won\'t book interviews then.</p>')
        for busy in person["busy_times"]:
            text_col, remove_col = st.columns([4, 1], vertical_alignment="center")
            text_col.html(f"<p>{busy['start_time']} to {busy['end_time'][11:]} · {escape(busy['reason'] or 'Busy')}</p>")
            if remove_col.button("Remove", key=f"busy_{busy['id']}", icon=":material/delete:"):
                delete_busy_time(busy["id"], person["id"], user["email"])
                st.rerun(scope="fragment")

        date_col, from_col, to_col = st.columns(3)
        day = date_col.date_input("Date", key=f"busy_day_{person['id']}")
        start = from_col.time_input("From", value=time(9, 0), key=f"busy_from_{person['id']}")
        end = to_col.time_input("To", value=time(17, 0), key=f"busy_to_{person['id']}")
        reason = st.text_input("Reason", placeholder="Annual leave", key=f"busy_reason_{person['id']}")
        if st.button("Add busy time", icon=":material/event_busy:"):
            if start >= end:
                st.error("The start time must be before the end time.", icon=":material/error:")
            else:
                add_busy_time(person["id"], datetime.combine(day, start).strftime("%Y-%m-%d %H:%M"),
                              datetime.combine(day, end).strftime("%Y-%m-%d %H:%M"), reason, user["email"])
                st.rerun(scope="fragment")


list_tab, add_tab = st.tabs(["All employees", "Add employee"])

# ---------- Tab 1: everyone, with an Edit button on each row ----------
with list_tab:
    if not employees:
        st.html(empty_state("badge", "No employees yet", "Open the Add employee tab to add interviewers and other staff."))

    for e in employees:
        with st.container(key=f"card-person-{e['id']}"):
            info_col, zone_col, status_col, edit_col = st.columns([3, 1.3, 2.2, 0.8], vertical_alignment="center")
            team = f" · {escape(e['team'])}" if e["team"] else ""
            info_col.html(f"""
                <div class="who {'' if e['is_active'] else 'off'}">{avatar(e['name'], 'sm')}
                    <div><b>{escape(e['name'])}</b><br><small>{escape(e['email'])} · {escape(e['role'])}{team}</small></div>
                </div>
            """)
            zone_col.html(f"<small>{e['timezone']}</small>")
            interview = pill(f"Interviews · {len(e['free_times'])} free times", "violet") if e["can_interview"] else ""
            active = pill("Active", "green") if e["is_active"] else pill("Turned off", "gray")
            status_col.html(f"{active} {interview}")
            if edit_col.button("Edit", key=f"edit_{e['id']}", icon=":material/edit:", width="stretch"):
                edit_employee(e["id"])

# ---------- Tab 2: add a new person (an empty form) ----------
with add_tab:
    with st.container(key="card-form"):
        employee_form({})
