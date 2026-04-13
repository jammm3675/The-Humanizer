# Pinkie Ape AI Agent

Pinkie Ape — это ироничный AI-агент для Telegram, интегрированный с Supabase и Groq. Маскот коллекции NOTAPES.

## Особенности
- **Memory System:** Помнит диалоги, строит краткие резюме (каждые 15 сообщ.) и обновляет портрет личности пользователя (каждые 40 сообщ.).
- **Agent Loop:** Итеративный цикл принятия решений (3-5 итераций) для проверки контекста и стиля.
- **NFT Context:** Автоматически подтягивает флор и статы коллекции с Getgems.
- **Group Safety:** Умные триггеры и защита от спама в группах.
- **Production-ready:** Heartbeat, Health Check (/health) и фоновые задачи.

## Архитектура
- `bot.py`: Входная точка и фоновые задачи.
- `services/agent_loop.py`: Мозг агента.
- `services/memory_service.py`: Управление памятью и AI-анализ.
- `services/db_service.py`: Supabase CRUD.
- `services/ai_service.py`: Groq LLM интеграция.

## Установка
1. Клонируйте репозиторий.
2. Установите зависимости: `pip install -r requirements.txt`
3. Настройте `.env` (см. `.env.example`).
4. Примените SQL схему из `schema.sql` в Supabase SQL Editor.

## Запуск
```bash
python bot.py
```
