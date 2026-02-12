# Pinkie Ape Bot (NOTAPES)

An AI-powered Telegram bot

## Features
- **Persona**: Ironic intellectual
- **Profiling**: Automatically analyzes and updates user personality traits every 5 messages.
- **Triggers**: Responds to @mentions (100%), Replies to bot (100%), and keywords (10-20% chance).
- **Memory**: Automatic conversation summarization every 20 messages to optimize context.
- **Keep-alive**: Built-in health check and keep-alive to stay active on Render Free Tier.

## Structure
- `bot.py`: Entry point, web server, and keep-alive.
- `database.py`: Supabase database interactions.
- `ai_engine.py`: Groq.
- `handlers/`: Telegram message handlers.
- `utils.py`: Helper functions (trigger logic).
