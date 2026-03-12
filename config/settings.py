import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GETGEMS_API_KEY = os.getenv("GETGEMS_API_KEY")
    TON_COLLECTION_ADDRESS = os.getenv("TON_COLLECTION_ADDRESS")
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
    ELEVEN_VOICE_ID = os.getenv("ELEVEN_VOICE_ID")
    RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")
    PORT = int(os.getenv("PORT", 8080))

    def __init__(self, model_config_name="default"):
        self.model_config_name = model_config_name

    def get_chat_model_params(self):
        return {}

    def get_chatbot_params(self):
        return {}

config = Config(os.getenv("MODEL_CONFIG_NAME", "default"))
