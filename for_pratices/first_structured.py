import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

llm = init_chat_model(
    model=os.environ["LLM_MODEL"],
    model_provider=os.environ["LLM_PROVIDER"],
)

# The shape of the answer I want
class SkillScore(BaseModel):
    skill: str
    # Guidence or Ai. Like number should be 0 to 5 
    level: int = Field(ge=0, le=5, description="0 means not found")
    evidence: str = Field(description="A short line copied from the resume")

prompt = ChatPromptTemplate.from_messages([
    ("system", "Rate the skill from 0 to 5 using only the resume text."),
    ("human", "Skill: {skill}\n\nResume: {resume}"),
])

# No StrOutputParser here. The answer comes back as a SkillScore.
chain = prompt | llm.with_structured_output(SkillScore)

result = chain.invoke({
    "skill": "Python",
    "resume": "Built 3 FastAPI services in Python at my last job.",
})

print(result)
print(result.level)
