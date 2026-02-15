import asyncio
import os
from unittest.mock import MagicMock, AsyncMock, patch

# Mock environment for imports
os.environ['SUPABASE_URL'] = 'https://haxljqdpvlfjekvmfgym.supabase.co'
os.environ['SUPABASE_SERVICE_ROLE_KEY'] = 'mock_key'
os.environ['GROQ_API_KEY'] = 'mock_key'
os.environ['TELEGRAM_BOT_TOKEN'] = 'mock_token'

async def test():
    print("Testing imports and methods existence...")
    try:
        from services.db_service import register_chat, get_active_groups
        from services.ai_service import ai_service
        import services.db_service as db_service

        print("Imports successful.")

        # Test methods existence
        assert callable(register_chat)
        assert callable(get_active_groups)
        assert hasattr(ai_service, 'generate_interjection')

        print("Method checks passed.")

        # Mock supabase client
        db_service.supabase = MagicMock()
        mock_table = db_service.supabase.table.return_value

        # Test register_chat logic
        print("Testing register_chat logic...")
        await register_chat(12345, "group")
        db_service.supabase.table.assert_called_with("chats")
        mock_table.upsert.assert_called_with({"chat_id": 12345, "chat_type": "group"})

        # Test get_active_groups logic
        print("Testing get_active_groups logic...")
        mock_table.select.return_value.in_.return_value.execute.return_value.data = [{"chat_id": 123}, {"chat_id": 456}]
        groups = await get_active_groups()
        assert groups == [123, 456]

        # Test generate_interjection logic
        print("Testing generate_interjection logic...")
        ai_service._client = AsyncMock()
        mock_completion = AsyncMock()
        mock_completion.choices = [MagicMock(message=MagicMock(content="Test Interjection"))]
        ai_service._client.chat.completions.create.return_value = mock_completion

        interjection = await ai_service.generate_interjection("Lore content")
        assert interjection == "Test Interjection"

        print("All logic tests passed!")

    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())
