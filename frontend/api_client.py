# The only file in the frontend that talks to my FastAPI backend.
# Pages call these functions. They never use requests themselves.
import json
import os

import requests

# Where the backend runs. I can change it with an API_URL line in .env
API_URL = os.environ.get("API_URL", "http://localhost:8000")
START_COMMAND = "uv run uvicorn app.api.main:app --reload"


# One clear error type, so a page can show the message to the user
class ApiError(Exception):
    pass


# Sends a request and gives back the JSON answer, or raises ApiError with a simple message
def send(method, path, **kwargs):
    try:
        response = requests.request(method, f"{API_URL}{path}", timeout=180, **kwargs)
    except requests.ConnectionError:
        raise ApiError(f"The backend is not running. Start it in a second terminal: {START_COMMAND}")
    except requests.Timeout:
        raise ApiError("The backend took too long to answer. Please try again.")

    if response.status_code != 200:
        # FastAPI puts the error message in "detail"
        try:
            detail = response.json().get("detail", response.text)
        except ValueError:
            detail = response.text
        raise ApiError(str(detail))
    return response.json()


# True when the backend is up
def is_running():
    try:
        send("GET", "/health")
        return True
    except ApiError:
        return False


# Logs in. Gives back {"id", "name", "email", "role"}, or raises ApiError
def login(email, password):
    return send("POST", "/auth/login", json={"email": email, "password": password})


# Makes a new HR account and gives back the same details as login
def signup(name, email, password):
    return send("POST", "/auth/signup", json={"name": name, "email": email, "password": password})


# Agent 1: scores one CV for one job.
# cv_file and job_file are Streamlit uploads. skills is a list of dictionaries
def score_cv(position, skills, cv_file, job_text="", job_file=None):
    files = {"cv_file": (cv_file.name, cv_file.getvalue(), cv_file.type)}
    if job_file is not None:
        files["job_file"] = (job_file.name, job_file.getvalue(), job_file.type)

    data = {
        "position": position,
        "skills": json.dumps(skills),
        "job_text": job_text,
    }
    return send("POST", "/resume-scoring/score", data=data, files=files)
