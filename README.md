# SHRI AI Platform

Baseline multi-agent backend scaffold using FastAPI.

## Features

- Chat agent with short-term memory and optional Supabase persistence
- Research agent with lightweight web search
- Automation agent for email tasks and image prompt generation
- Typed API contracts with FastAPI/Pydantic

## Project Structure

- `app/main.py`: FastAPI app entrypoint
- `api/chat_api.py`: chat endpoints
- `api/automation_api.py`: automation + research endpoints
- `agents/*`: core orchestration logic
- `tools/*`: integrations and task utilities
- `memory/memory_manager.py`: local + optional DB-backed memory
- `database/supabase_client.py`: optional Supabase adapter
- `config/settings.py`: env-driven settings

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Optional `.env`:

```env
APP_ENV=development
SUPABASE_URL=
SUPABASE_KEY=
SMTP_HOST=
SMTP_PORT=587
SMTP_USERNAME=
SMTP_PASSWORD=
DEFAULT_FROM_EMAIL=noreply@example.com
```

## Run

```bash
uvicorn app.main:app --reload
```

## API Endpoints

- `GET /health`
- `POST /chat/`
  - body: `{"user_id":"u1","message":"hello"}`
- `POST /automation/task`
  - email body example:
    `{"task_type":"send_email","payload":{"to":"a@b.com","subject":"Hi","body":"Test"}}`
  - image prompt example:
    `{"task_type":"image_prompt","payload":{"subject":"a futuristic city","style":"watercolor"}}`
- `POST /automation/research`
  - body: `{"query":"latest AI agents"}`
