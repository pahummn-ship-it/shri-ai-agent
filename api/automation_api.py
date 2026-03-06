from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from agents.automation_agent import AutomationAgent
from agents.research_agent import ResearchAgent

router = APIRouter(prefix="/automation", tags=["automation"])

_automation_agent = AutomationAgent()
_research_agent = ResearchAgent()


class AutomationRequest(BaseModel):
    task_type: str = Field(min_length=1)
    payload: dict[str, str] = Field(default_factory=dict)


class ResearchRequest(BaseModel):
    query: str = Field(min_length=1)


@router.post("/task")
async def run_task(request: AutomationRequest) -> dict[str, Any]:
    return await _automation_agent.run(task_type=request.task_type, payload=request.payload)


@router.post("/research")
async def research(request: ResearchRequest) -> dict[str, Any]:
    return await _research_agent.run(query=request.query)
