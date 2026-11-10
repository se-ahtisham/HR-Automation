# Call results: what each candidate said on the script agent's call, and the summary. HR reads them here
import json
from html import escape

import streamlit as st

from app.core.candidates import list_candidates
from components import card_title, empty_state, icon_list, load_page_css, page_header, status_badge

load_page_css(__file__)
page_header("Call results", "The script agent's answers and summary for every candidate it called.", section="Hiring")

called = [c for c in list_candidates() if c["call_status"] == "Done"]

if not called:
    st.html(empty_state("call", "No calls yet",
                        "Approve a candidate for calling, then click Call on their profile in Candidates."))
    st.stop()

for c in called:
    answers = json.loads(c["answers"] or "{}")
    said = [
        f"<b>Consent:</b> {escape(c['consent_status'] or '-')}",
        f"<b>Available for interview:</b> {escape(c['candidate_availability'] or 'Not given')}",
        f"<b>Previous job:</b> {escape(answers.get('previous_job') or 'Not given')}",
        f"<b>Why they want to shift:</b> {escape(answers.get('reason_for_shift') or 'Not given')}",
    ]
    with st.container(key=f"card-call-{c['id']}"):
        st.html(f'<p class="call-name">{escape(c["name"])}</p>'
                f'<p class="call-meta">{escape(c["job_title"])} · Score {c["total_score"]}/100</p>{status_badge(c["current_status"])}')
        said_col, summary_col = st.columns(2)
        said_col.html(card_title("record_voice_over", "What they said", "mi-green") + icon_list(said, "check"))
        summary_col.html(card_title("summarize", "Summary of the call") + f"<p>{escape(c['summary'] or '')}</p>")
