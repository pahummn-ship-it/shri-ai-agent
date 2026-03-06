from __future__ import annotations

from memory.memory_manager import MemoryManager


class ChatAgent:
    def __init__(self, memory_manager: MemoryManager) -> None:
        self.memory = memory_manager

    async def run(self, user_id: str, message: str) -> dict[str, str]:
        self.memory.add(user_id=user_id, role="user", content=message)
        history = self.memory.history(user_id=user_id, limit=5)

        # Simple baseline response; swap with LLM invocation when needed.
        response = (
            f"You said: {message}\n"
            f"I remember {len(history)} recent messages in this session."
        )
        self.memory.add(user_id=user_id, role="assistant", content=response)
        return {"response": response}
