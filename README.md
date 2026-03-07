# SHRI AI Platform

## Model Routing (OpenRouter)

Set these in Railway Variables (or `.env`) to enable automatic model fallback:

```env
OPENROUTER_API_KEY=your_key
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL_CANDIDATES=deepseek/deepseek-chat,meta-llama/llama-3.1-8b-instruct,mistralai/mistral-7b-instruct,google/gemma-7b-it
```

Behavior:
- App tries models in listed order.
- If a model returns `402 Payment Required`, app automatically tries next model.
