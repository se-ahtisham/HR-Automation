# The FastAPI app. The web pages DON'T use it: they call my Python code directly.
# It is only for webhooks: web addresses that OUTSIDE services send data to, which Streamlit can't receive.
#   POST /webhooks/elevenlabs   ElevenLabs sends this when a screening call ends (app/api/webhooks.py)
# Run it next to the app, in a 2nd terminal:
#   uv run uvicorn app.api.main:app --port 8000
# ElevenLabs must reach it from the internet, so while testing on my computer I open a tunnel (ngrok, see elevenlabs.md)
from fastapi import FastAPI

from app.api.webhooks import router

app = FastAPI(
    title="Nexora Hire webhooks",
    description="Receives data from outside services: the ElevenLabs call results.",
)
app.include_router(router)


# A quick check that the server is running
@app.get("/health")
def health():
    return {"status": "ok"}
