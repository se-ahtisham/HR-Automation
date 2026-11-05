# Screening calls: Agent 2's call, the transcript, the summary, and HR stop #2
import streamlit as st

from components import card_title, empty_state, icon, icon_list, load_page_css, page_header, pill, status_badge

load_page_css(__file__)
page_header("Screening calls", "Agent 2 calls approved candidates and asks the job questions.", section="Hiring")

# Real data comes from the backend later (Agent 2, Day 5). Until then every list is empty
JOBS = []
CANDIDATES = []
TRANSCRIPT = []
CALL_SUMMARY = {"said": [], "unclear": [], "ai_thinks": []}

# Only candidates that HR approved for screening can get a call
ready = [c for c in CANDIDATES if c["status"] in
         ["Approved for Screening", "Screening Pending", "Screening Completed (HR Review)"]]
if not ready:
    st.html(empty_state("call", "No one to call yet",
                        "Approve a candidate for screening on the Candidates page. They show here for the call."))
    st.stop()

names = [c["name"] for c in ready]
picked = st.selectbox("Candidate", names, index=len(names) - 1)
c = [p for p in ready if p["name"] == picked][0]
job = [j for j in JOBS if j["id"] == c["job_id"]][0]

# ---------- Call box ----------
with st.container(key="card-call"):
    info_col, mode_col, button_col = st.columns([2, 1.3, 1], vertical_alignment="center")
    info_col.html(f"""
        <p class="call-name">{c['name']}</p>
        <p class="call-meta">{job['title']} &nbsp;·&nbsp; {icon('call')} {c['phone']}</p>
        {status_badge(c['status'])}
    """)
    mode = mode_col.radio("Call type", ["Pretend call", "Real call"], horizontal=True)
    if button_col.button("Start call", type="primary", icon=":material/call:", width="stretch"):
        if mode == "Real call":
            st.warning("Real calls only go to my own test phone, never to a real candidate.")
        st.toast("MOCK: no call is made yet.", icon=":material/call:")

    # The safety checks of the call
    st.html(f"""
        <div class="checks">
            <span>{pill(icon("check") + " Said it is an AI", "green")}</span>
            <span>{pill(icon("check") + " Recording consent: yes", "green")}</span>
            <span>{pill(icon("check") + " Job questions only", "green")}</span>
            <span>{pill("Human asked: no", "gray")}</span>
            <span>{pill("Tries: 1 of 3", "gray")}</span>
        </div>
    """)

transcript_col, summary_col = st.columns([1.3, 1])

# ---------- The transcript as chat bubbles ----------
with transcript_col:
    with st.container(key="card-transcript", height=520):
        st.html('<p class="section-title">Transcript</p>')
        bubbles = ""
        for line in TRANSCRIPT:
            who = "AI assistant" if line["who"] == "ai" else "Candidate"
            bubbles += f'<div class="bubble bubble-{line["who"]}"><small>{who}</small>{line["text"]}</div>'
        st.html(f'<div class="chat">{bubbles}</div>')

# ---------- The summary, in separate parts ----------
with summary_col:
    with st.container(key="card-said"):
        st.html(card_title("record_voice_over", "What the candidate said", "mi-green") + icon_list(CALL_SUMMARY["said"], "check"))
    with st.container(key="card-unclear"):
        st.html(card_title("help", "Not clear", "mi-amber") + icon_list(CALL_SUMMARY["unclear"], "priority_high"))
    with st.container(key="card-thinks"):
        st.html(card_title("psychology", "What the AI thinks") + icon_list(CALL_SUMMARY["ai_thinks"], "remove"))

# ---------- HR decision (HR stop #2) ----------
with st.container(key="card-decision"):
    st.html('<p class="section-title">Your decision</p>')
    reason = st.text_area("Reason (required)", placeholder="Why did you decide this?")
    col1, col2, _ = st.columns([1, 1, 1])
    approve = col1.button("Approve for interview", type="primary", icon=":material/check:", width="stretch")
    decline = col2.button("Decline", icon=":material/close:", width="stretch")
    if approve or decline:
        if reason.strip():
            st.toast("MOCK: your decision is not saved yet.", icon=":material/check_circle:")
        else:
            st.error("Please write a reason first.")
