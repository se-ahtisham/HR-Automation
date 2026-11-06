# The ElevenLabs webhook: when a call ends, ElevenLabs sends a message here, and the answers are saved by themselves
# (HR doesn't need to click "Get the call result"). Needs ELEVENLABS_WEBHOOK_SECRET in .env
from fastapi import APIRouter, HTTPException, Request

from app.agents.script_agent.agent import get_call_result, read_webhook
from app.agents.script_agent.save_call import save_call_result, save_no_answer
from app.core.database.database import get_one

router = APIRouter()


@router.post("/webhooks/elevenlabs")
async def call_ended(request: Request):
    # 1. Is it really from ElevenLabs? The signature is checked on the raw text, before reading it
    try:
        event = read_webhook((await request.body()).decode(), request.headers.get("elevenlabs-signature", ""))
    except Exception:
        raise HTTPException(status_code=401, detail="Bad or missing signature")

    # 2. Which candidate? My app saved the call's id when the call started
    conversation_id = event.get("data", {}).get("conversation_id")
    call = get_one("SELECT candidate_id FROM screenings WHERE conversation_id = :id", {"id": conversation_id})
    if call is None:
        return {"saved": False, "why": "Not one of my calls"}    # 200, so ElevenLabs doesn't send it again

    # 3. Save it. "Already saved" if HR's button was faster
    if event.get("type") == "call_initiation_failure":
        tries, limit = save_no_answer(call.candidate_id, conversation_id, "ElevenLabs webhook")
        return {"saved": True, "result": f"No answer, try {tries} of {limit}"}
    result = get_call_result(conversation_id)
    if result is None or result.get("no_answer"):
        return {"saved": False, "why": "The call isn't finished yet"}
    return {"saved": True, "result": save_call_result(call.candidate_id, conversation_id, result, "ElevenLabs webhook")}
