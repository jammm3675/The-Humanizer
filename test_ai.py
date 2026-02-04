import asyncio
import os
from ai_engine import generate_response

async def test():
    if not os.environ.get("GEMINI_API_KEY"):
        print("Skipping AI test: GEMINI_API_KEY not set")
        return

    user_data = {
        "username": "testuser",
        "personality_traits": {"vibe": "ape"},
        "conversation_summary": ""
    }
    try:
        response = await generate_response("LFG! To the moon!", user_data)
        print(f"AI Response: {response}")
    except Exception as e:
        print(f"AI Error: {e}")

if __name__ == "__main__":
    asyncio.run(test())
