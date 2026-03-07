from __future__ import annotations

import os
import secrets
from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/control", tags=["control-panel"])


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _require_admin(x_admin_key: str | None) -> None:
    expected = os.getenv("SHRI_ADMIN_KEY", "").strip()
    if not expected:
        # Dev mode fallback when admin key is not configured.
        return
    if x_admin_key != expected:
        raise HTTPException(status_code=401, detail="Invalid admin key.")


class AgentCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    description: str = Field(default="", max_length=500)
    system_prompt: str = Field(default="You are a helpful AI assistant.", max_length=4000)


class AgentUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=80)
    description: str | None = Field(default=None, max_length=500)
    system_prompt: str | None = Field(default=None, max_length=4000)
    active: bool | None = None


class AgentResponse(BaseModel):
    agent_id: str
    name: str
    description: str
    system_prompt: str
    api_key: str
    active: bool
    created_at: str
    updated_at: str


class ChannelConnectRequest(BaseModel):
    channel_type: Literal["website", "whatsapp", "android_app"] = "website"
    config: dict[str, Any] = Field(default_factory=dict)


class ChannelConnectionResponse(BaseModel):
    agent_id: str
    channel_type: str
    config: dict[str, Any]
    connected_at: str


class UsageEventRequest(BaseModel):
    event_type: Literal["chat_request", "chat_response", "error", "tool_call"]
    meta: dict[str, Any] = Field(default_factory=dict)


AGENTS: dict[str, dict[str, Any]] = {}
CHANNELS: dict[str, dict[str, dict[str, Any]]] = {}
USAGE_LOGS: dict[str, list[dict[str, Any]]] = {}


@router.get("/health")
def control_health() -> dict[str, str]:
    return {"status": "ok", "service": "control-panel"}


@router.post("/agents", response_model=AgentResponse)
def create_agent(payload: AgentCreateRequest, x_admin_key: str | None = Header(default=None)) -> AgentResponse:
    _require_admin(x_admin_key)

    agent_id = str(uuid4())
    now = _now_iso()
    record = {
        "agent_id": agent_id,
        "name": payload.name,
        "description": payload.description,
        "system_prompt": payload.system_prompt,
        "api_key": f"shri_{secrets.token_urlsafe(24)}",
        "active": True,
        "created_at": now,
        "updated_at": now,
    }
    AGENTS[agent_id] = record
    CHANNELS[agent_id] = {}
    USAGE_LOGS[agent_id] = []
    return AgentResponse(**record)


@router.get("/agents", response_model=list[AgentResponse])
def list_agents(x_admin_key: str | None = Header(default=None)) -> list[AgentResponse]:
    _require_admin(x_admin_key)
    return [AgentResponse(**agent) for agent in AGENTS.values()]


@router.get("/agents/{agent_id}", response_model=AgentResponse)
def get_agent(agent_id: str, x_admin_key: str | None = Header(default=None)) -> AgentResponse:
    _require_admin(x_admin_key)
    if agent_id not in AGENTS:
        raise HTTPException(status_code=404, detail="Agent not found.")
    return AgentResponse(**AGENTS[agent_id])


@router.patch("/agents/{agent_id}", response_model=AgentResponse)
def update_agent(
    agent_id: str,
    payload: AgentUpdateRequest,
    x_admin_key: str | None = Header(default=None),
) -> AgentResponse:
    _require_admin(x_admin_key)
    if agent_id not in AGENTS:
        raise HTTPException(status_code=404, detail="Agent not found.")

    record = AGENTS[agent_id]
    updates = payload.model_dump(exclude_none=True)
    record.update(updates)
    record["updated_at"] = _now_iso()
    AGENTS[agent_id] = record
    return AgentResponse(**record)


@router.delete("/agents/{agent_id}")
def delete_agent(agent_id: str, x_admin_key: str | None = Header(default=None)) -> dict[str, str]:
    _require_admin(x_admin_key)
    if agent_id not in AGENTS:
        raise HTTPException(status_code=404, detail="Agent not found.")

    AGENTS.pop(agent_id, None)
    CHANNELS.pop(agent_id, None)
    USAGE_LOGS.pop(agent_id, None)
    return {"status": "deleted", "agent_id": agent_id}


@router.post("/agents/{agent_id}/channels", response_model=ChannelConnectionResponse)
def connect_channel(
    agent_id: str,
    payload: ChannelConnectRequest,
    x_admin_key: str | None = Header(default=None),
) -> ChannelConnectionResponse:
    _require_admin(x_admin_key)
    if agent_id not in AGENTS:
        raise HTTPException(status_code=404, detail="Agent not found.")

    connected_at = _now_iso()
    record = {
        "agent_id": agent_id,
        "channel_type": payload.channel_type,
        "config": payload.config,
        "connected_at": connected_at,
    }
    CHANNELS.setdefault(agent_id, {})
    CHANNELS[agent_id][payload.channel_type] = record
    AGENTS[agent_id]["updated_at"] = connected_at
    return ChannelConnectionResponse(**record)


@router.get("/agents/{agent_id}/channels", response_model=list[ChannelConnectionResponse])
def list_channels(agent_id: str, x_admin_key: str | None = Header(default=None)) -> list[ChannelConnectionResponse]:
    _require_admin(x_admin_key)
    if agent_id not in AGENTS:
        raise HTTPException(status_code=404, detail="Agent not found.")
    return [ChannelConnectionResponse(**v) for v in CHANNELS.get(agent_id, {}).values()]


@router.delete("/agents/{agent_id}/channels/{channel_type}")
def disconnect_channel(
    agent_id: str,
    channel_type: str,
    x_admin_key: str | None = Header(default=None),
) -> dict[str, str]:
    _require_admin(x_admin_key)
    if agent_id not in AGENTS:
        raise HTTPException(status_code=404, detail="Agent not found.")

    channels = CHANNELS.get(agent_id, {})
    if channel_type not in channels:
        raise HTTPException(status_code=404, detail="Channel not connected.")

    channels.pop(channel_type, None)
    AGENTS[agent_id]["updated_at"] = _now_iso()
    return {"status": "disconnected", "agent_id": agent_id, "channel_type": channel_type}


@router.post("/agents/{agent_id}/usage")
def add_usage_event(
    agent_id: str,
    payload: UsageEventRequest,
    x_admin_key: str | None = Header(default=None),
) -> dict[str, str]:
    _require_admin(x_admin_key)
    if agent_id not in AGENTS:
        raise HTTPException(status_code=404, detail="Agent not found.")

    event = {
        "event_id": str(uuid4()),
        "event_type": payload.event_type,
        "meta": payload.meta,
        "created_at": _now_iso(),
    }
    USAGE_LOGS.setdefault(agent_id, [])
    USAGE_LOGS[agent_id].append(event)
    return {"status": "logged", "event_id": event["event_id"]}


@router.get("/agents/{agent_id}/usage")
def get_usage_events(
    agent_id: str,
    limit: int = 50,
    x_admin_key: str | None = Header(default=None),
) -> dict[str, Any]:
    _require_admin(x_admin_key)
    if agent_id not in AGENTS:
        raise HTTPException(status_code=404, detail="Agent not found.")

    safe_limit = min(max(limit, 1), 200)
    events = USAGE_LOGS.get(agent_id, [])[-safe_limit:]
    return {"agent_id": agent_id, "count": len(events), "events": events}
