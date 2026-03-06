from __future__ import annotations

from tools.email_tool import EmailTool
from tools.image_tool import ImageTool


class AutomationAgent:
    def __init__(self) -> None:
        self.email_tool = EmailTool()
        self.image_tool = ImageTool()

    async def run(self, task_type: str, payload: dict[str, str]) -> dict[str, str]:
        if task_type == "send_email":
            required = ("to", "subject", "body")
            if any(not payload.get(key) for key in required):
                return {"status": "error", "message": "Missing required email fields: to, subject, body."}
            return self.email_tool.send_email(
                to=payload["to"],
                subject=payload["subject"],
                body=payload["body"],
            )

        if task_type == "image_prompt":
            if not payload.get("subject"):
                return {"status": "error", "message": "Missing required field: subject."}
            result = self.image_tool.generate_prompt(
                subject=payload["subject"], style=payload.get("style")
            )
            return {"status": "ok", "message": result["note"], "prompt": result["prompt"]}

        return {"status": "error", "message": f"Unsupported task_type: {task_type}"}
