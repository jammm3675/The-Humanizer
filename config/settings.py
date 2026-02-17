import os
import yaml
from dotenv import load_dotenv

load_dotenv()

class Config:
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    TON_API_KEY = os.getenv("TON_API_KEY")
    GETGEMS_API_KEY = os.getenv("GETGEMS_API_KEY")
    TON_COLLECTION_ADDRESS = os.getenv("TON_COLLECTION_ADDRESS")
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
    ELEVEN_VOICE_ID = os.getenv("ELEVEN_VOICE_ID")
    RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")
    PORT = int(os.getenv("PORT", 8080))

    def __init__(self, model_config_name="default"):
        self.model_config_name = model_config_name
        self.models_config = self._load_models_config()
        self.current_model = self.models_config.get("models", {}).get(model_config_name, {})

    def _load_models_config(self):
        config_path = os.path.join(os.path.dirname(__file__), "models.yml")
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        return {}

    def get_chat_model_params(self):
        return self.current_model.get("chat_model", {})

    def get_chatbot_params(self):
        return self.current_model.get("chatbot", {})

config = Config(os.getenv("MODEL_CONFIG_NAME", "default"))
