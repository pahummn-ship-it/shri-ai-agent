from __future__ import annotations

from collections import defaultdict, deque
from typing import Any

from database.supabase_client import SupabaseClient


class MemoryManager:
    def __init__(self, max_messages: int = 50) -> None:
        self._messages: dict[str, deque[dict[str, str]]] = defaultdict(lambda: deque(maxlen=max_messages))
        self._db = SupabaseClient()

    def add(self, user_id: str, role: str, content: str) -> None:
        entry = {"role": role, "content": content}
        self._messages[user_id].append(entry)
        self._db.save_memory(user_id=user_id, role=role, content=content)

    def history(self, user_id: str, limit: int = 10) -> list[dict[str, str]]:
        local = list(self._messages[user_id])[-limit:]
        if local:
            return local

        remote: list[dict[str, Any]] = self._db.fetch_memory(user_id=user_id, limit=limit)
        remote.reverse()
        normalized: list[dict[str, str]] = [
            {"role": str(item.get("role", "assistant")), "content": str(item.get("content", ""))}
            for item in remote
        ]
        for msg in normalized:
            self._messages[user_id].append(msg)
        return normalized
