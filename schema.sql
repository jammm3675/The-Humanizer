-- Supabase SQL Schema
CREATE TABLE users (
    telegram_id BIGINT PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    personality_traits JSONB DEFAULT '{"status": "Stranger", "trust_level": 30, "last_topic": "None"}'::jsonb,
    conversation_summary TEXT DEFAULT '',
    message_count INTEGER DEFAULT 0,
    last_messages JSONB DEFAULT '[]'::jsonb,
    is_admin BOOLEAN DEFAULT FALSE,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE chats (
    chat_id BIGINT PRIMARY KEY,
    chat_type TEXT,
    title TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE global_config (
    key TEXT PRIMARY KEY,
    content TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE messages (
    id BIGSERIAL PRIMARY KEY,
    telegram_id BIGINT REFERENCES users(telegram_id),
    chat_id BIGINT,
    role TEXT,
    content TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE summaries (
    id BIGSERIAL PRIMARY KEY,
    telegram_id BIGINT REFERENCES users(telegram_id),
    summary_text TEXT,
    traits_snapshot JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
