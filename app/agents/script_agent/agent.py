# The script agent: phones a candidate, gets back the answers and the summary, and checks ElevenLabs' webhooks.
# Everything switches on with .env only:
#   ELEVENLABS_PHONE_NUMBER_ID  my Twilio number in ElevenLabs. Missing = pretend calls (MOCK), typed by HR
#   TEST_PHONE_NUMBERS          the only numbers a real call may go to, like "+923001234567,+923211234567"
#   ELEVENLABS_WEBHOOK_SECRET   checks that a webhook really came from ElevenLabs
import os

from dotenv import load_dotenv
from elevenlabs import ConversationInitiationClientDataRequestInput, ElevenLabs

load_dotenv()

# The key comes from .env. I pass it myself, because the SDK looks for it before load_dotenv() runs
client = ElevenLabs(api_key=os.environ["ELEVENLABS_API_KEY"])


# Real calls only when my Twilio number is in .env. Otherwise HR types a pretend call
def calls_are_real():
    return bool(os.environ.get("ELEVENLABS_PHONE_NUMBER_ID"))


# Safety: a real call goes only to a number on my test list (never to a real candidate by mistake)
def is_test_number(phone):
    allowed = [number.strip().replace(" ", "") for number in os.environ.get("TEST_PHONE_NUMBERS", "").split(",")]
    return phone.replace(" ", "") in allowed


# Phones the candidate. Gives back the call's id on ElevenLabs
def call_candidate(phone, name, job_title):
    if not is_test_number(phone):
        raise ValueError(f"{phone} is not in TEST_PHONE_NUMBERS in .env, so it is not called.")
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


# Gets the finished call. None = still busy. {"no_answer": True} = the call never connected
def get_call_result(conversation_id):
    call = client.conversational_ai.conversations.get(conversation_id=conversation_id)
    if call.status == "failed":
        return {"no_answer": True}
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
        "wants_human": answers.get("wants_human"),
        "needs_other_way": answers.get("needs_other_way"),
        # A short summary of the whole talk, so HR can read it
        "summary": analysis.transcript_summary,
    }


# A webhook from ElevenLabs: the SDK checks the signature (a bad or old one raises an error) and gives back the event
def read_webhook(raw_body, signature):
    return client.webhooks.construct_event(raw_body, signature, os.environ.get("ELEVENLABS_WEBHOOK_SECRET", ""))
