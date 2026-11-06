import os
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Load my settings from .env
load_dotenv()

# Set up the AI
llm = init_chat_model(
    model=os.environ["LLM_MODEL"],
    model_provider=os.environ["LLM_PROVIDER"],
)

# The form with a blank
prompt = ChatPromptTemplate.from_template("Explain {topic} in simple words.")

# Join the steps: fill the form, ask the AI, get plain text
chain = prompt | llm | StrOutputParser()

result = chain.invoke({"topic": "Machine Learning"})
print(result)
