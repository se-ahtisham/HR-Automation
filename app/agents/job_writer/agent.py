# The AI Job Post Writer: a short idea -> a full job draft that HR reads and edits before saving
import os
from typing import Literal

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from app.agents.job_writer.prompts import JOB_WRITER_PROMPT

load_dotenv()


# One skill in the draft
class DraftSkill(BaseModel):
    name: str
    type: Literal["Must-have", "Nice-to-have"]
    required_level: int = Field(ge=1, le=5)


# The answer the AI must give back
class JobDraft(BaseModel):
    title: str
    level: Literal["Junior", "Mid", "Senior", "Team Lead"]
    location: str
    work_type: Literal["Office", "Remote", "Hybrid"]
    min_experience: int = Field(ge=0, le=30)
    job_post: str
    skills: list[DraftSkill]


# The job writer has its own Groq key, so it doesn't use up Agent 1's free limit
llm = init_chat_model(
    model=os.environ["LLM_MODEL"],
    model_provider=os.environ["LLM_PROVIDER"],
    api_key=os.environ["GROQ_JOB_WRITER_API_KEY"],
    max_tokens=3000,
)

prompt = ChatPromptTemplate.from_messages([
    ("system", JOB_WRITER_PROMPT),
    ("human", "My idea: {idea}"),
])


# Writes a job draft from a short idea. Gives back a JobDraft, or None if all 3 AI tries fail
def write_job_post(idea):
    chain = prompt | llm.with_structured_output(JobDraft, method="json_schema", strict=True)
    chain = chain.with_retry(stop_after_attempt=3)
    try:
        return chain.invoke({"idea": idea})
    except Exception:
        return None
