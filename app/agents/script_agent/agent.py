# The script agent: phones a candidate, and later gets back the answers and the summary of the call
import os

from dotenv import load_dotenv
from elevenlabs import ConversationInitiationClientDataRequestInput, ElevenLabs

load_dotenv()

# The key comes from .env. I pass it myself, because the SDK looks for it before load_dotenv() runs
client = ElevenLabs(api_key=os.environ["ELEVENLABS_API_KEY"])


# Phones the candidate. Gives back the call's id on ElevenLabs.
# ELEVENLABS_PHONE_NUMBER_ID = my Twilio phone number, added to ElevenLabs
def call_candidate(phone, name, job_title):
    call = client.conversational_ai.twilio.outbound_call(
        agent_id=os.environ["ELEVENLABS_AGENT_ID"],
        agent_phone_number_id=os.environ["ELEVENLABS_PHONE_NUMBER_ID"],
        to_number=phone,
        # Fills in {{candidate_name}} and {{job_title}} in prompts.py
        conversation_initiation_client_data=ConversationInitiationClientDataRequestInput(
            dynamic_variables={"candidate_name": name, "job_title": job_title},
        ),
    )
    return call.conversation_id


# Gets the finished call. Gives back None while ElevenLabs is still busy with it
def get_call_result(conversation_id):
    call = client.conversational_ai.conversations.get(conversation_id=conversation_id)
    analysis = call.analysis
    if call.status != "done" or analysis is None:
        return None

    # The answers ElevenLabs pulled out of the call. .get() gives None if one wasn't found
    answers = {name: item.value for name, item in (analysis.data_collection_results or {}).items()}
    return {
        "consent_given": answers.get("consent_given"),
        "available_date_time": answers.get("available_date_time"),
        "previous_job": answers.get("previous_job"),
        "reason_for_shift": answers.get("reason_for_shift"),
        # A short summary of the whole talk, so HR can read it
        "summary": analysis.transcript_summary,
    }
