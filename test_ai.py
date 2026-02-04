import asyncio
import os
from ai_engine import generate_response, update_personality

async def test():
    if not os.environ.get("GEMINI_API_KEY"):
        print("Skipping AI test: GEMINI_API_KEY not set")
        return

    user_data = {
        "username": "testuser",
        "personality_traits": {"vibe": "ape"},
        "conversation_summary": ""
    }

    print("Testing generate_response...")
    try:
        response = await generate_response("LFG! To the moon!", user_data)
        print(f"AI Response: {response}")
    except Exception as e:
        print(f"AI Response Error: {e}")

    print("\nTesting update_personality...")
    try:
        conversation = "User: LFG! To the moon!\nThe Humanizer: How primitive. You should focus on the lore."
        traits = await update_personality(conversation)
        print(f"Updated Traits: {traits}")
    except Exception as e:
        print(f"Personality Update Error: {e}")

if __name__ == "__main__":
    asyncio.run(test())
