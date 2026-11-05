# The FastAPI app. The web pages DON'T use it: they call my Python code directly.
# It is only for webhooks: web addresses that OUTSIDE services send data to, which Streamlit can't receive.
#   Day 5:  ElevenLabs sends the call transcript when a call ends
#   Day 11: the online CV form sends each new CV
# Run it only when I build those:
#   uv run uvicorn app.api.main:app --reload
from fastapi import FastAPI

app = FastAPI(
    title="Nexora Hire webhooks",
    description="Receives data from outside services: ElevenLabs call results (Day 5) and the online CV form (Day 11).",
)


# A quick check that the server is running
@app.get("/health")
def health():
    return {"status": "ok"}
