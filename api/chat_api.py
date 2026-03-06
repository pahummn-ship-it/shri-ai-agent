from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from agents.chat_agent import ChatAgent
from memory.memory_manager import MemoryManager

router = APIRouter(prefix="/chat", tags=["chat"])

_memory = MemoryManager()
_chat_agent = ChatAgent(memory_manager=_memory)


class ChatRequest(BaseModel):
    user_id: str = Field(min_length=1)
    message: str = Field(min_length=1)


class ChatResponse(BaseModel):
    response: str


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    result = await _chat_agent.run(user_id=request.user_id, message=request.message)
    return ChatResponse(response=result["response"])
