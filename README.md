# The Humanizer Telegram Bot (NOTAPES)

An AI-powered Telegram bot that ironicly guides "crypto-apes" to "human lore".

## Features
- **Persona**: Ironic intellectual guiding users through evolution, biology, and philosophy.
- **Profiling**: Automatically analyzes and updates user personality traits every 5 messages.
- **Voice**: Generates male voice responses using `edge-tts`.
- **Triggers**: Responds to @mentions (100%) and keywords (15%+ chance).
- **Keep-alive**: Built-in health check and keep-alive to stay active on Render Free Tier.

## Deployment Guide

### 1. Google AI Studio (Gemini)
1. Go to [Google AI Studio](https://aistudio.google.com/).
2. Create or sign in to your Google account.
3. Click on **"Get API key"** in the sidebar.
4. Create a new API key for a project.
5. Copy this key into `GEMINI_API_KEY` in your `.env`.

### 2. Supabase Setup
1. Create a new project at [Supabase](https://supabase.com/).
2. Go to **Project Settings** -> **API**.
3. Copy the **Project URL** into `SUPABASE_URL`.
4. Copy the **service_role** key (Secret) into `SUPABASE_SERVICE_ROLE_KEY`.
5. Go to the **SQL Editor** and run the following script:
   ```sql
   CREATE TABLE IF NOT EXISTS users (
       telegram_id BIGINT PRIMARY KEY,
       username TEXT,
       bio_info TEXT,
       personality_traits JSONB DEFAULT '{}'::jsonb,
       conversation_summary TEXT DEFAULT '',
       message_count INTEGER DEFAULT 0,
       voice_count INTEGER DEFAULT 0,
       created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
   );
   ```

### 3. Render Setup & Keep-alive
1. Create a new **Web Service** on [Render](https://render.com/).
2. Connect your repository.
3. Set the **Runtime** to `Python 3`.
4. Add the following **Environment Variables**:
   - `TELEGRAM_BOT_TOKEN`: From @BotFather.
   - `SUPABASE_URL`: From Supabase.
   - `SUPABASE_SERVICE_ROLE_KEY`: From Supabase.
   - `GEMINI_API_KEY`: From Google AI Studio.
   - `RENDER_EXTERNAL_URL`: The URL Render gives you (e.g., `https://my-bot.onrender.com`).
5. Render will automatically run the bot. The bot includes a `/health` endpoint and a background task that pings itself every 10 minutes to prevent sleeping.

### 4. Installation
If running locally:
```bash
pip install -r requirements.txt
python bot.py
```

## Structure
- `bot.py`: Entry point, web server, and keep-alive.
- `database.py`: Supabase database interactions.
- `ai_engine.py`: Gemini 1.5 Flash logic.
- `voice_engine.py`: edge-tts voice generation.
- `handlers/`: Telegram message handlers.
- `utils.py`: Helper functions (trigger logic).
