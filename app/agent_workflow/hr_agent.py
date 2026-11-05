import os
import sqlite3
from typing import TypedDict
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.types import interrupt

from app.agents.resume_scoring.agent import score_cv

load_dotenv()


# What the HR agent keeps for one candidate
class CandidateState(TypedDict):
    position: str
    job_post: str
    resume_text: str
    cv_result: dict
    hr_answer: str


# Step 1: call the resume scoring agent
def resume_scoring_agent(state):
    result = score_cv(state["position"], state["job_post"], "Python, SQL, Git", state["resume_text"])
    return {"cv_result": result.model_dump()}


# Step 2: wait for HR to say yes or no
def hr_review(state):
    answer = interrupt("Approve this candidate for a screening call?")
    return {"hr_answer": answer}


# Join the steps: START → resume_scoring_agent → hr_review → END
builder = StateGraph(CandidateState)
builder.add_node("resume_scoring_agent", resume_scoring_agent)
builder.add_node("hr_review", hr_review)
builder.add_edge(START, "resume_scoring_agent")
builder.add_edge("resume_scoring_agent", "hr_review")
builder.add_edge("hr_review", END)

# Saves each candidate's place while waiting for HR
conn = sqlite3.connect(os.environ["CHECKPOINT_DB_PATH"], check_same_thread=False)
hr_agent = builder.compile(checkpointer=SqliteSaver(conn))
