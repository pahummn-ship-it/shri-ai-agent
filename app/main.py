import ast
import os
import socket
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from redis import Redis
from redis.exceptions import RedisError
import requests

load_dotenv()

app = FastAPI(title=os.getenv("APP_NAME", "SHRI_AI"))


class ChatRequest(BaseModel):
    user_id: str = Field(min_length=1)
    message: str = Field(min_length=1)


class RedisMemory:
    def __init__(self, ttl_seconds: int = 86400) -> None:
        self.ttl_seconds = ttl_seconds
        self._fallback: dict[str, list[dict[str, str]]] = defaultdict(list)
        self._fallback_summary: dict[str, str] = {}
        self._redis: Redis | None = None

        redis_url = os.getenv("REDIS_URL")
        if not redis_url:
            return

        try:
            client = Redis.from_url(redis_url, decode_responses=True)
            client.ping()
            self._redis = client
        except RedisError:
            self._redis = None

    def _key(self, user_id: str) -> str:
        return f"chat:history:{user_id}"

    def _summary_key(self, user_id: str) -> str:
        return f"chat:summary:{user_id}"

    def get(self, user_id: str, limit: int = 20) -> list[dict[str, str]]:
        if self._redis is None:
            return self._fallback[user_id][-limit:]

        raw_items = self._redis.lrange(self._key(user_id), -limit, -1)
        history: list[dict[str, str]] = []
        for item in raw_items:
            role, _, content = item.partition("|")
            if role and content:
                history.append({"role": role, "content": content})
        return history

    def add(self, user_id: str, role: str, content: str) -> None:
        if self._redis is None:
            self._fallback[user_id].append({"role": role, "content": content})
            self._fallback[user_id] = self._fallback[user_id][-20:]
            return

        key = self._key(user_id)
        self._redis.rpush(key, f"{role}|{content}")
        self._redis.ltrim(key, -20, -1)
        self._redis.expire(key, self.ttl_seconds)

    def get_summary(self, user_id: str) -> str:
        if self._redis is None:
            return self._fallback_summary.get(user_id, "")
        summary = self._redis.get(self._summary_key(user_id))
        return summary or ""

    def set_summary(self, user_id: str, summary: str) -> None:
        if self._redis is None:
            self._fallback_summary[user_id] = summary
            return
        key = self._summary_key(user_id)
        self._redis.set(key, summary)
        self._redis.expire(key, self.ttl_seconds)


memory = RedisMemory()


@tool
def get_server_time() -> str:
    """Get current UTC server time in ISO format."""
    return datetime.now(timezone.utc).isoformat()


@tool
def calculator(expression: str) -> str:
    """Safely evaluate a basic arithmetic expression like (2+3)*4."""
    allowed_nodes = {
        ast.Expression,
        ast.BinOp,
        ast.UnaryOp,
        ast.Add,
        ast.Sub,
        ast.Mult,
        ast.Div,
        ast.Pow,
        ast.Mod,
        ast.USub,
        ast.UAdd,
        ast.Constant,
        ast.Load,
    }

    parsed = ast.parse(expression, mode="eval")
    for node in ast.walk(parsed):
        if type(node) not in allowed_nodes:
            raise ValueError("Unsupported expression. Only basic arithmetic is allowed.")

    result = eval(compile(parsed, "<calculator>", "eval"), {"__builtins__": {}}, {})
    return str(result)


def get_llm() -> tuple[ChatOpenAI, str]:
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    if openrouter_key:
        base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
        model = os.getenv("LLM_MODEL", "deepseek/deepseek-chat")
        return ChatOpenAI(api_key=openrouter_key, base_url=base_url, model=model, temperature=0), model

    if openai_key:
        model = os.getenv("LLM_MODEL", "gpt-4o-mini")
        return ChatOpenAI(api_key=openai_key, model=model, temperature=0), model

    raise HTTPException(status_code=500, detail="Set OPENROUTER_API_KEY or OPENAI_API_KEY in .env")


def _to_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    return str(content)


def _history_to_messages(history: list[dict[str, str]]) -> list[Any]:
    out: list[Any] = []
    for msg in history:
        role = msg.get("role", "assistant")
        content = msg.get("content", "")
        if role == "user":
            out.append(HumanMessage(content=content))
        else:
            out.append(AIMessage(content=content))
    return out


def update_summary(llm: ChatOpenAI, user_id: str, user_text: str, assistant_text: str) -> str:
    previous_summary = memory.get_summary(user_id)
    summary_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                (
                    "Update the conversation summary. Keep it short, factual, and useful for future replies. "
                    "Preserve user preferences and unresolved tasks."
                ),
            ),
            (
                "human",
                (
                    "Previous summary:\n{previous_summary}\n\n"
                    "New user message:\n{user_text}\n\n"
                    "Assistant reply:\n{assistant_text}\n\n"
                    "Return only updated summary."
                ),
            ),
        ]
    )
    try:
        summary_messages = summary_prompt.format_messages(
            previous_summary=previous_summary or "No prior summary.",
            user_text=user_text,
            assistant_text=assistant_text,
        )
        summary_response = llm.invoke(summary_messages)
        new_summary = _to_text(summary_response.content).strip()
        if new_summary:
            memory.set_summary(user_id, new_summary)
            return new_summary
    except Exception:
        pass
    return previous_summary


@app.get("/")
def home() -> dict[str, str]:
    return {"message": "SHRI AI Agent Running"}


@app.get("/diag/provider")
def diag_provider() -> dict[str, Any]:
    checks: dict[str, Any] = {}
    targets = {
        "openrouter": "https://openrouter.ai/api/v1/models",
        "openai": "https://api.openai.com/v1/models",
    }

    for name, url in targets.items():
        host = url.split("/")[2]
        item: dict[str, Any] = {"host": host}
        try:
            item["dns_ip"] = socket.gethostbyname(host)
        except Exception as exc:
            item["dns_error"] = f"{type(exc).__name__}: {exc}"

        try:
            resp = requests.get(url, timeout=8)
            item["http_status"] = resp.status_code
        except Exception as exc:
            item["http_error"] = f"{type(exc).__name__}: {exc}"

        checks[name] = item

    return checks


@app.post("/chat")
def chat(req: ChatRequest) -> dict[str, Any]:
    llm, model = get_llm()
    llm_with_tools = llm.bind_tools([get_server_time, calculator])

    history = memory.get(req.user_id, limit=20)
    summary = memory.get_summary(req.user_id)

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                (
                    "You are SHRI AI. Be concise and practical. "
                    "Use tools when needed for arithmetic or current server time.\n\n"
                    "Conversation summary:\n{summary}"
                ),
            ),
            MessagesPlaceholder("history"),
            ("human", "{user_input}"),
        ]
    )
    messages: list[Any] = prompt.format_messages(
        summary=summary or "No prior summary.",
        history=_history_to_messages(history),
        user_input=req.message,
    )

    try:
        ai_message = llm_with_tools.invoke(messages)
        final_text = _to_text(ai_message.content)

        if ai_message.tool_calls:
            tool_map = {t.name: t for t in [get_server_time, calculator]}
            tool_messages: list[ToolMessage] = []

            for tool_call in ai_message.tool_calls:
                tool_name = tool_call.get("name", "")
                tool_args = tool_call.get("args") or {}
                tool_id = tool_call.get("id", tool_name)

                if tool_name not in tool_map:
                    tool_result = f"Unknown tool: {tool_name}"
                else:
                    try:
                        tool_result = tool_map[tool_name].invoke(tool_args)
                    except Exception as exc:
                        tool_result = f"Tool error: {exc}"

                tool_messages.append(ToolMessage(content=str(tool_result), tool_call_id=tool_id))

            final_message = llm_with_tools.invoke(messages + [ai_message, *tool_messages])
            final_text = _to_text(final_message.content)

    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"LLM request failed ({type(exc).__name__}): {exc}") from exc

    memory.add(req.user_id, "user", req.message)
    memory.add(req.user_id, "assistant", final_text)
    updated_summary = update_summary(llm, req.user_id, req.message, final_text)

    return {
        "user_id": req.user_id,
        "model": model,
        "response": final_text,
        "summary": updated_summary,
        "tools_enabled": ["get_server_time", "calculator"],
        "history_count": len(memory.get(req.user_id, limit=20)),
    }

