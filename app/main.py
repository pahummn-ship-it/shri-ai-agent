from fastapi import FastAPI
from pydantic import BaseModel
import requests
import os

app = FastAPI(title="SHRI AI")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

class ChatRequest(BaseModel):
    message: str

@app.get("/")
def home():
    return {"message": "SHRI AI Agent Running"}

@app.post("/chat")
def chat(req: ChatRequest):

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "deepseek/deepseek-chat",
            "messages": [
                {"role": "user", "content": req.message}
            ]
        }
    )

    return response.json()
