from __future__ import annotations
import os, json
from typing import Any, Dict, List
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

#TODO (Extension): add support for other LLM providers

class LLM:
    def __init__(self, model: str | None = None, temperature: float = 0.2):
        self.client = OpenAI(api_key=os.getenv("AI_API_KEY"))
        self.model = model or os.getenv("MODEL", "gpt-4o-mini")
        self.temperature = temperature

    def chat(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        no use native tool-calling. The model returns a JSON controller in content.
        """
        resp = self.client.chat.completions.create(
            model=self.model,
            temperature=self.temperature,
            messages=messages,
            # Don't provide tools and force JSON output from the model.
            response_format={"type": "json_object"},
        )

        choice = resp.choices[0]
        raw = choice.message.content or "{}"

        try:
            msg = json.loads(raw)
        except Exception:
            # If the model ever returns non-JSON, surface it as a write action
            msg = {"action": "write", "report": raw, "confidence": 0.0}

        action = (msg.get("action") or "").lower().strip()
        tool_calls: List[Dict[str, Any]] = []
        content = ""

        if action == "call":
            # Normalize calls to [{"tool": str, "args": dict}, ...]
            calls = msg.get("calls") or []
            norm = []
            for c in calls:
                if not isinstance(c, dict):
                    continue
                # Since there is no more defined schema
                # Accept various keys for tool name and args
                tool = c.get("tool") or c.get("name") or c.get("recipient_name")
                args = c.get("args") or c.get("arguments") or c.get("parameters") or {}
                if tool:
                    norm.append({"tool": tool, "args": args})
            tool_calls = norm
            # Keep short reasoning in content for logs (optional)
            content = (msg.get("reasoning") or msg.get("why") or "").strip()

        elif action == "write":
            content = (msg.get("report") or "").strip()
            tool_calls = []

        else:
            # Unknown / malformed → just pass through
            content = (msg.get("report") or msg.get("reasoning") or "").strip()
            tool_calls = []

        return {
            "type": action or "unknown",
            "content": content,
            "tool_calls": tool_calls,  # ALWAYS a list
            "finish_reason": choice.finish_reason,
            "id": resp.id,
            "raw_controller": msg, # for DEBUGGING
        }
