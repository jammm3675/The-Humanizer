# The Humanizer Telegram Bot (NOTAPES)

An AI-powered Telegram bot that ironicly guides "crypto-apes" to "human lore".

## Features
- **Persona**: Ironic intellectual guiding users through evolution, biology, and philosophy.
- **Profiling**: Automatically analyzes and updates user personality traits every 5 messages.
- **Voice**: Generates male voice responses using `edge-tts`.
- **Triggers**: Responds to @mentions (100%), Replies to bot (100%), and keywords (10-20% chance).
- **Memory**: Automatic conversation summarization every 20 messages to optimize context.
- **Keep-alive**: Built-in health check and keep-alive to stay active on Render Free Tier.

## Structure
- `bot.py`: Entry point, web server, and keep-alive.
- `database.py`: Supabase database interactions.
- `ai_engine.py`: Gemini 2.0 Flash logic.
- `voice_engine.py`: edge-tts voice generation.
- `handlers/`: Telegram message handlers.
- `utils.py`: Helper functions (trigger logic).
