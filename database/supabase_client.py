from __future__ import annotations

from typing import Any

from config.settings import get_settings

try:
    from supabase import Client, create_client
except Exception:  # pragma: no cover - optional dependency at runtime
    Client = Any  # type: ignore[assignment]
    create_client = None  # type: ignore[assignment]


class SupabaseClient:
    def __init__(self) -> None:
        settings = get_settings()
        self._enabled = bool(settings.supabase_url and settings.supabase_key and create_client)
        self._client: Client | None = None
        if self._enabled:
            self._client = create_client(settings.supabase_url, settings.supabase_key)  # type: ignore[arg-type]

    @property
    def enabled(self) -> bool:
        return self._enabled

    def save_memory(self, user_id: str, role: str, content: str) -> None:
        if not self._client:
            return
        self._client.table("memory").insert(
            {"user_id": user_id, "role": role, "content": content}
        ).execute()

    def fetch_memory(self, user_id: str, limit: int = 10) -> list[dict[str, Any]]:
        if not self._client:
            return []
        result = (
            self._client.table("memory")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return list(result.data or [])
