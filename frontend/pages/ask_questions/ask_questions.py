# Ask questions: the only page a CANDIDATE sees. They open it from the secret link in their email (?token=...).
# The ElevenLabs script agent talks to them in the browser and asks the 4 questions. No login, no HR menu.
import json
import os
from html import escape

import streamlit as st

from app.agents.script_agent.web_call import LINK_OPEN, candidate_by_token, save_web_call
from components import card_title, load_page_css

load_page_css(__file__)

candidate = candidate_by_token(st.query_params.get("token"))

with st.container(key="ask-shell"):
    st.html('<p class="brand">Nexora Hire</p>')

    # A wrong or old link
    if candidate is None:
        st.html('<h1 class="hello">This link doesn\'t work</h1>'
                '<p class="lead">Please open the link from your email again, or reply to that email.</p>')
        st.stop()

    # The answers are saved already (or HR has moved on)
    if candidate["current_status"] not in LINK_OPEN:
        st.html(f'<h1 class="hello">Thank you, {escape(candidate["name"])}!</h1>'
                '<p class="lead">We have your answers. Our HR team will email you about the next step.</p>')
        st.stop()

    st.html(f'<h1 class="hello">Hello {escape(candidate["name"])}</h1>'
            f'<p class="lead">Congratulations! You are in the next step for the <b>{escape(candidate["job_title"])}</b> job.</p>'
            + card_title("record_voice_over", "Talk to our AI assistant (about 1 minute)") +
            '<ol class="steps">'
            '<li>Click the button below and allow the microphone.</li>'
            '<li>Answer 3 short questions, and say your available date and time for the interview.</li>'
            '<li>When the assistant says goodbye, click <b>I have finished</b>.</li>'
            '</ol>'
            '<p class="note">The talk is recorded so our HR team can read your answers. An AI assistant asks the '
            'questions; a person in HR makes every decision.</p>')

    # The ElevenLabs widget. It gives the agent the candidate's name, the job and the candidate's id (to find the talk later).
    # The name comes from a CV (untrusted text), so it is escaped before it goes into the HTML
    variables = {"candidate_name": candidate["name"], "job_title": candidate["job_title"],
                 "candidate_id": str(candidate["id"])}
    st.iframe(f"""
        <elevenlabs-convai agent-id="{escape(os.environ['ELEVENLABS_AGENT_ID'])}" variant="expanded"
                           dynamic-variables='{escape(json.dumps(variables), quote=True)}'></elevenlabs-convai>
        <script src="https://unpkg.com/@elevenlabs/convai-widget-embed" async type="text/javascript"></script>
    """, height=520)

    if st.button("I have finished", type="primary", icon=":material/check_circle:", width="stretch"):
        with st.spinner("Saving your answers..."):
            result = save_web_call(candidate["id"], "candidate")
        if result in ("Saved", "Already saved"):
            st.rerun()
        elif result == "No talk yet":
            st.warning("We can't find your talk yet. Please talk to the assistant first, then click again.",
                       icon=":material/mic_off:")
        else:
            st.info("Your talk is still being processed. Please wait a few seconds and click again.",
                    icon=":material/hourglass_top:")
