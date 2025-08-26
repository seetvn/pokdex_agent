# agents/observations.py
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class Observation:
    """A single tool invocation + outcome."""
    tool: str
    args: Dict[str, Any]
    result: Optional[Any] = None
    error: Optional[str] = None
    step: Optional[int] = None
    started_at: float = field(default_factory=time.time)
    ended_at: Optional[float] = None

    # --- lifecycle -----------------------------------------------------------

    def finish(self, *, result: Any | None = None, error: str | None = None) -> None:
        """Mark observation as finished, optionally setting result or error."""
        self.ended_at = time.time()
        if result is not None:
            self.result = result
        if error is not None:
            self.error = error

    # --- convenience ---------------------------------------------------------

    @property
    def ok(self) -> bool:
        return self.error is None

    @property
    def duration_ms(self) -> Optional[int]:
        if self.ended_at is None:
            return None
        return int((self.ended_at - self.started_at) * 1000)

    # --- serialisation for controller ---------------------------------------

    def to_message_payload(self) -> Dict[str, Any]:
        """
        Shape expected by your controller:
        {
          "tool": "...",
          "args": {...},
          "result": {...}  # or {"error": "..."}
        }
        """
        payload: Dict[str, Any] = {"tool": self.tool, "args": self.args}
        payload["result"] = self.result if self.ok else {"error": self.error}
        return payload

    def to_json(self) -> str:
        return json.dumps(self.to_message_payload(), ensure_ascii=False)

    def short_payload(self, max_chars: int = 4000) -> Dict[str, Any]:
        """
        Produce a payload that won't explode your token budget.
        Truncates large string results; collapses huge dicts.
        """
        payload = self.to_message_payload()
        as_text = json.dumps(payload, ensure_ascii=False)
        if len(as_text) <= max_chars:
            return payload

        # Truncate aggressively
        res = payload.get("result")
        if isinstance(res, str):
            payload["result"] = res[: max_chars // 2] + "… (truncated)"
        elif isinstance(res, dict):
            # Keep top-level keys but mark as truncated
            payload["result"] = {"_truncated": True}
        else:
            payload["result"] = "(truncated)"
        return payload

    # --- logging helpers (optional) -----------------------------------------

    def log(self, console=None, *, verbose: bool = False, pretty_printer=None) -> None:
        """
        Console-friendly log. If you pass your print_observation as pretty_printer,
        it will render the result on verbose mode.
        """
        if console is None:
            return
        try:
            from rich.markdown import Markdown
            dur = f"{self.duration_ms} ms" if self.duration_ms is not None else "—"
            console.print(Markdown(
                f"**Tool:** `{self.tool}`  •  **ok:** `{self.ok}`  •  **duration:** `{dur}`"
            ))
        except Exception:
            console.print(f"Tool={self.tool} ok={self.ok} duration={self.duration_ms}ms")

        if verbose and pretty_printer:
            pretty_printer(self.result if self.ok else {"error": self.error})

    # --- factory methods -----------------------------------------------------

    @staticmethod
    def success(tool: str, args: Dict[str, Any], result: Any, *, step: int | None = None) -> "Observation":
        obs = Observation(tool=tool, args=args, step=step)
        obs.finish(result=result)
        return obs

    @staticmethod
    def failure(tool: str, args: Dict[str, Any], error: str, *, step: int | None = None) -> "Observation":
        obs = Observation(tool=tool, args=args, step=step)
        obs.finish(error=error)
        return obs
