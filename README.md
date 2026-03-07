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
