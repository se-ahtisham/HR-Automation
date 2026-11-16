# The script agent on ElevenLabs: gets back the answers and the summary of a finished talk.
# The talk itself happens in the candidate's browser (web_call.py and the Ask questions page). No phone, no Twilio
import os

from dotenv import load_dotenv
from elevenlabs import ElevenLabs

load_dotenv()

# The key comes from .env. I pass it myself, because the SDK looks for it before load_dotenv() runs
client = ElevenLabs(api_key=os.environ["ELEVENLABS_API_KEY"])


# Gets the finished talk. None = still busy. {"no_answer": True} = the talk failed
def get_call_result(conversation_id):
    call = client.conversational_ai.conversations.get(conversation_id=conversation_id)
    if call.status == "failed":
        return {"no_answer": True}
    analysis = call.analysis
    if call.status != "done" or analysis is None:
        return None

    # The answers ElevenLabs pulled out of the talk. .get() gives None if one wasn't found
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
