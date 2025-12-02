import os
import signal
import sys
from dotenv import load_dotenv

from elevenlabs.client import ElevenLabs
from elevenlabs.conversational_ai.conversation import Conversation
from elevenlabs.conversational_ai.default_audio_interface import DefaultAudioInterface
from websockets.exceptions import ConnectionClosedError

load_dotenv()

agent_id = os.getenv("AGENT_ID")
api_key = os.getenv("ELEVENLABS_API_KEY")

# Validate environment variables
if not agent_id or not api_key:
    print("Error: AGENT_ID and ELEVENLABS_API_KEY must be set in .env file")
    sys.exit(1)

elevenlabs = ElevenLabs(api_key=api_key)

conversation = Conversation(
    # API client and agent ID.
    elevenlabs,
    agent_id,

    # Assume auth is required when API_KEY is set.
    requires_auth=bool(api_key),

    # Use the default audio interface.
    audio_interface=DefaultAudioInterface(),

    # Simple callbacks that print the conversation to the console.
    callback_agent_response=lambda response: print(f"Agent: {response}"),
    callback_agent_response_correction=lambda original, corrected: print(f"Agent: {original} -> {corrected}"),
    callback_user_transcript=lambda transcript: print(f"User: {transcript}"),

    # Uncomment if you want to see latency measurements.
    callback_latency_measurement=lambda latency: print(f"Latency: {latency}ms"),
)

# Setup graceful shutdown
def signal_handler(sig, frame):
    print("\nShutting down gracefully...")
    try:
        conversation.end_session()
    except Exception as e:
        print(f"Error during shutdown: {e}")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# Start the conversation with error handling
try:
    print("Starting conversation...")
    conversation.start_session()
    conversation_id = conversation.wait_for_session_end()
    print(f"Conversation ended. ID: {conversation_id}")
    
except ConnectionClosedError as e:
    error_message = str(e)
    if "quota limit" in error_message.lower():
        print("\n❌ ERROR: ElevenLabs quota exceeded!")
        print("Please check your account at https://elevenlabs.io")
        print("You may need to:")
        print("  - Upgrade your plan")
        print("  - Purchase additional credits")
        print("  - Wait for your quota to reset")
    else:
        print(f"\n❌ Connection error: {error_message}")
    sys.exit(1)
    
except KeyboardInterrupt:
    print("\nInterrupted by user")
    try:
        conversation.end_session()
    except:
        pass
    sys.exit(0)
    
except Exception as e:
    print(f"\n❌ Unexpected error: {type(e).__name__}: {e}")
    try:
        conversation.end_session()
    except:
        pass
    sys.exit(1)