from __future__ import annotations


class ImageTool:
    def generate_prompt(self, subject: str, style: str | None = None) -> dict[str, str]:
        chosen_style = style or "cinematic"
        prompt = f"High quality {chosen_style} image of {subject}, highly detailed, 4k"
        return {"prompt": prompt, "note": "Connect this prompt to your preferred image model provider."}
