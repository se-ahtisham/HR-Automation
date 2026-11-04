import os
import sqlite3
from typing import TypedDict
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.types import interrupt

load_dotenv()


# The small note that travels through the flow
class HiringState(TypedDict, total=False):
    candidate_id: int
    hr_decision: str


# The steps. They are empty for now
def extract(state):
    print("Step: read the CV")
    return {}


def score(state):
    print("Step: score the CV")
    return {}


def screen(state):
    print("Step: make the screening call")
    return {}


def schedule(state):
    print("Step: find an interview time")
    return {}


def send(state):
    print("Step: send the invite email")
    return {}


# The 3 HR stops. Each one pauses the flow and waits for HR
def hr_gate_1(state):
    decision = interrupt("Approve this candidate for a call?")
    return {"hr_decision": decision}


def hr_gate_2(state):
    decision = interrupt("Approve this candidate for an interview?")
    return {"hr_decision": decision}


def hr_gate_3(state):
    decision = interrupt("Send this invite email?")
    return {"hr_decision": decision}


# After each HR stop, "yes" goes on and "no" ends the flow
def hr_answer(state):
    return state["hr_decision"]


# Join the steps in order
builder = StateGraph(HiringState)

builder.add_node("extract", extract)
builder.add_node("score", score)
builder.add_node("hr_gate_1", hr_gate_1)
builder.add_node("screen", screen)
builder.add_node("hr_gate_2", hr_gate_2)
builder.add_node("schedule", schedule)
builder.add_node("hr_gate_3", hr_gate_3)
builder.add_node("send", send)

builder.add_edge(START, "extract")
builder.add_edge("extract", "score")
builder.add_edge("score", "hr_gate_1")
builder.add_conditional_edges("hr_gate_1", hr_answer, {"yes": "screen", "no": END})
builder.add_edge("screen", "hr_gate_2")
builder.add_conditional_edges("hr_gate_2", hr_answer, {"yes": "schedule", "no": END})
builder.add_edge("schedule", "hr_gate_3")
builder.add_conditional_edges("hr_gate_3", hr_answer, {"yes": "send", "no": END})
builder.add_edge("send", END)

# The checkpointer saves my place, so a restart doesn't lose progress
conn = sqlite3.connect(os.environ["CHECKPOINT_DB_PATH"], check_same_thread=False)
graph = builder.compile(checkpointer=SqliteSaver(conn))
