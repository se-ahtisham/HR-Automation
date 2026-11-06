# Agent 3, the scheduler: 2 small AI chains.
# 1. read_availability: the candidate's words from the call → time windows
# 2. write_invite: the interview invite email (HR reads it before it is sent)
import os
from datetime import datetime, timedelta

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel

from app.agents.scheduling.free_times import now_here
from app.agents.scheduling.prompts import AVAILABILITY_PROMPT, INVITE_PROMPT

load_dotenv()

llm = init_chat_model(model=os.environ["LLM_MODEL"], model_provider=os.environ["LLM_PROVIDER"],
                      max_tokens=1500, reasoning_effort="low", temperature=0)


# The answers the AI must give back. Times look like "2026-11-10 15:00"
class TimeWindow(BaseModel):
    start: str
    end: str


class CandidateTimes(BaseModel):
    windows: list[TimeWindow]


class InviteEmail(BaseModel):
    subject: str
    body: str


# prompt | llm, like my other agents. 3 tries if the AI fails
availability_chain = (
    ChatPromptTemplate.from_messages([("system", AVAILABILITY_PROMPT), ("human", "The candidate said: <words>{words}</words>")])
    | llm.with_structured_output(CandidateTimes, method="json_schema", strict=True)
).with_retry(stop_after_attempt=3)

invite_chain = (
    ChatPromptTemplate.from_messages([("system", INVITE_PROMPT),
                                      ("human", "Candidate: {name}\nJob: {job}\nWhen: {when} ({timezone})\nLength: {minutes} minutes\n"
                                                "How: {meeting_type}\nInterviewer: {interviewer}")])
    | llm.with_structured_output(InviteEmail, method="json_schema", strict=True)
).with_retry(stop_after_attempt=3)


# Gives back [(start, end), ...]. Empty if the AI fails or finds no usable time.
# The AI gets a ready calendar ("Wednesday 2026-11-11"), because LLMs often get weekdays wrong
def read_availability(words, settings):
    today = now_here(settings)
    days = "\n".join((today + timedelta(days=n)).strftime("%A %Y-%m-%d") for n in range(settings["booking_days"] + 1))
    try:
        answer = CandidateTimes.model_validate(availability_chain.invoke(
            {"words": words, "today": today.strftime("%A %Y-%m-%d"), "days": days, "timezone": settings["timezone"]}))
        return [(datetime.fromisoformat(w.start), datetime.fromisoformat(w.end)) for w in answer.windows]
    except Exception:
        return []


# Gives back {"subject", "body"}. If the AI fails, an empty body that HR writes by hand
def write_invite(name, job, slot, settings):
    try:
        return InviteEmail.model_validate(invite_chain.invoke({
            "name": name, "job": job, "when": datetime.fromisoformat(slot["start"]).strftime("%A %d %B %Y at %H:%M"),
            "timezone": settings["timezone"], "minutes": settings["interview_minutes"],
            "meeting_type": settings["meeting_type"], "interviewer": slot["interviewer"],
        })).model_dump()
    except Exception:
        return {"subject": f"Interview invite: {job}", "body": ""}
