from __future__ import annotations
import os, json
from typing import Any, Dict, List, Tuple
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

class LLM:
    def __init__(self, model: str | None = None, temperature: float = 0.2):
        self.client = OpenAI(api_key=os.getenv("AI_API_KEY"))
        self.model = model or os.getenv("MODEL", "gpt-4o-mini")
        self.temperature = temperature

    def chat(self, messages: List[Dict[str, str]], tools: List[Dict[str, Any]] | None = None) -> Dict[str, Any]:
        """
        Call Chat Completions with optional tool calling.
        Returns the whole response dict so the agent can inspect tool_calls or content.
        """
        resp = self.client.chat.completions.create(
            model=self.model,
            temperature=self.temperature,
            messages=messages,
            tools=tools or None,
            tool_choice="auto" if tools else "none",
        )
        # Convert to a basic dict we can serialise/log
        choice = resp.choices[0]
        msg = choice.message
        out = {
            "content": msg.content,
            "tool_calls": [tc.model_dump() for tc in (msg.tool_calls or [])],
            "finish_reason": choice.finish_reason,
            "id": resp.id,
        }
        return out
