# Ask your candidates: a chat that answers only from the CVs (RAG, Day 10 extra)
import streamlit as st

from components import load_page_css, page_header

load_page_css(__file__)
page_header("Ask your candidates", "Ask in normal words. Every answer shows the proof line from the CV.", section="Tools", tag="MOCK")

# The chat history lives in session_state, so it stays when the page reruns
if "chat" not in st.session_state:
    st.session_state.chat = []

# Quick question buttons
st.html('<p class="section-title">Try a question</p>')
col1, col2, col3 = st.columns(3)
quick = None
if col1.button("Who has led a team?", width="stretch"):
    quick = "Who has led a team?"
if col2.button("Who knows Docker?", width="stretch"):
    quick = "Who knows Docker?"
if col3.button("Who has AWS?", width="stretch"):
    quick = "Who has AWS?"

# Show all messages
for message in st.session_state.chat:
    avatar = ":material/person:" if message["role"] == "user" else ":material/auto_awesome:"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["text"])

# The box at the bottom of the page
question = st.chat_input("Ask about your candidates...") or quick

if question:
    st.session_state.chat.append({"role": "user", "text": question})
    st.session_state.chat.append({
        "role": "assistant",
        "text": "MOCK answer: the chat is not connected yet. On Day 10 it will search the CVs and "
                "answer with **Candidate #** and a proof line.",
    })
    st.rerun()

st.caption("Blind Mode is on, so the chat shows Candidate # instead of names. "
           "It refuses questions about age, gender, religion, family or health.")
