# The start file of my backend (FastAPI). Run it from the project root:
#   uv run uvicorn app.api.main:app --reload
# Then open http://localhost:8000/docs to try every web address in the browser.
from fastapi import FastAPI

from app.api import auth, resume_scoring

app = FastAPI(
    title="Nexora Hire API",
    description="The backend my Streamlit pages talk to. It runs my AI agents.",
)

# Each part has its own file of web addresses (a router). I add them here
app.include_router(auth.router)
app.include_router(resume_scoring.router)


# A quick check that the backend is running
@app.get("/health")
def health():
    return {"status": "ok"}
