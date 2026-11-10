# Makes (or updates) my script agent on ElevenLabs. Run it once, and again after I change prompts.py:
#   uv run python -m app.agents.script_agent.setup_agent
# The first run prints the new agent id. I put it in .env as ELEVENLABS_AGENT_ID
import os

from dotenv import load_dotenv
from elevenlabs import AgentPlatformSettingsRequestModel, ConversationalConfig, ElevenLabs

from app.agents.script_agent.prompts import DATA_TO_COLLECT, FIRST_MESSAGE, SYSTEM_PROMPT

load_dotenv()

# The key comes from .env. I pass it myself, because the SDK looks for it before load_dotenv() runs
client = ElevenLabs(api_key=os.environ["ELEVENLABS_API_KEY"])

# model_validate turns my dictionary into the SDK's own settings object
conversation_config = ConversationalConfig.model_validate({
    "agent": {
        "first_message": FIRST_MESSAGE,
        "language": "en",
        "prompt": {
            "prompt": SYSTEM_PROMPT,
            "llm": "gemini-2.5-flash",
            "max_tokens": 150,
            # Lets the agent hang up when the questions are done
            # end_call: hang up when the questions are done. voicemail_detection: hang up on an answering machine
            "built_in_tools": {
                "end_call": {"name": "end_call", "params": {"system_tool_type": "end_call"}},
                "voicemail_detection": {"name": "voicemail_detection", "params": {"system_tool_type": "voicemail_detection"}},
            },
        },
    },
    # The cheapest English voice
    "tts": {"voice_id": "EXAVITQu4vr4xnSDxMaL", "model_id": "eleven_flash_v2"},
    # Low limit: a call stops after 72 seconds (1.2 minutes), so the free ElevenLabs minutes (~15 a month) give about 10 calls
    "conversation": {"max_duration_seconds": 72},
})

platform_settings = AgentPlatformSettingsRequestModel.model_validate({
    # After the call, ElevenLabs pulls these answers out of the talk
    "data_collection": DATA_TO_COLLECT,
    # Low limit: 1 call at a time, 20 calls a day, never pay extra
    "call_limits": {"agent_concurrency_limit": 1, "daily_limit": 20, "bursting_enabled": False},
})

agent_id = os.environ.get("ELEVENLABS_AGENT_ID")
if agent_id:
    client.conversational_ai.agents.update(agent_id=agent_id, name="Nexora Hire - Script agent",
                                           conversation_config=conversation_config, platform_settings=platform_settings)
    print("Agent updated:", agent_id)
else:
    agent = client.conversational_ai.agents.create(name="Nexora Hire - Script agent", conversation_config=conversation_config,
                                                   platform_settings=platform_settings)
    print("Add this line to .env:")
    print(f"ELEVENLABS_AGENT_ID={agent.agent_id}")
