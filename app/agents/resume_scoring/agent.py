import os
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate

from app.agents.resume_scoring.prompts import (
    JUNIOR_PROMPT,
    MID_PROMPT,
    SENIOR_PROMPT,
    TEAM_LEAD_PROMPT,
)
from app.agents.resume_scoring.safety import CVResult

load_dotenv()

# max_tokens gives the AI enough room to finish its answer
llm = init_chat_model(
    model=os.environ["LLM_MODEL"],
    model_provider=os.environ["LLM_PROVIDER"],
    max_tokens=4000,
)


# Picks the prompt for the job's position
def pick_prompt(position):
    if position == "Junior":
        system_prompt = JUNIOR_PROMPT
    elif position == "Mid":
        system_prompt = MID_PROMPT
    elif position == "Senior":
        system_prompt = SENIOR_PROMPT
    else:
        system_prompt = TEAM_LEAD_PROMPT

    return ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "Evaluate this CV for a {position} job.\n\n"
                  "Job post:\n{job_post}\n\n"
                  "Skills to check:\n{skills}\n\n"
                  "<resume>\n{resume}\n</resume>"),
    ])


# Scores one CV: prompt | llm | parser
def score_cv(position, job_post, skills, resume_text):
    prompt = pick_prompt(position)
    chain = prompt | llm.with_structured_output(CVResult, method="json_schema", strict=True)
    chain = chain.with_retry(stop_after_attempt=3)

    # Send to AI. If all 3 tries fail, give back None, so a human checks this CV
    try:
        return chain.invoke({
            "position": position,
            "job_post": job_post,
            "skills": skills,
            "resume": resume_text,
        })
    except Exception:
        return None
