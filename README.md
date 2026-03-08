# SHRI AI Platform

## Model Routing (OpenRouter)

Set these in Railway Variables (or `.env`) to enable automatic model fallback:

```env
OPENROUTER_API_KEY=your_key
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL_CANDIDATES=openrouter/free,deepseek/deepseek-chat,openai/gpt-4o-mini
```

Behavior:
- App tries models in listed order.
- If a model returns `402` or `404`, app automatically tries next model.

## Control Panel API (Phase 1 Start)

Admin key:

```env
SHRI_ADMIN_KEY=change_this_to_secure_value
```

Pass this header on control-panel routes:

```http
X-Admin-Key: <SHRI_ADMIN_KEY>
```

Base routes:
- `GET /control/health`
- `POST /control/agents`
- `GET /control/agents`
- `GET /control/agents/{agent_id}`
- `PATCH /control/agents/{agent_id}`
- `DELETE /control/agents/{agent_id}`
- `POST /control/agents/{agent_id}/channels`
- `GET /control/agents/{agent_id}/channels`
- `DELETE /control/agents/{agent_id}/channels/{channel_type}`
- `POST /control/agents/{agent_id}/usage`
- `GET /control/agents/{agent_id}/usage?limit=50`

Supported channel types:
- `website`
- `whatsapp`
- `android_app`

DB schema for Supabase/Postgres:
- `database/control_panel_schema.sql`

## Website FAQ / RAG Support Mode

Knowledge source file:
- `knowledge/pahummn_faq.json`

Behavior in `/chat`:
- Retrieves top relevant FAQ blocks from `pahummn_faq.json`
- Forces responses to use only FAQ context
- If info is missing, bot replies:
  - `I don't have this information on pahummn.com yet.`
- Response includes `knowledge_hits` count

## Next Steps Status

### Core Build
- [x] Basic AI API
- [x] AI memory system (Redis + summary memory)
- [x] AI tools (calculator, server time)
- [x] Website chatbot
- [ ] Android app integration
- [ ] WhatsApp bot

### Control Panel (Dashboard)
- [x] Create agents API
- [x] Connect website API
- [x] Connect WhatsApp API
- [x] Connect app API (`android_app`)

### Vision
- [ ] Universal AI Agent Platform (full product stage)
