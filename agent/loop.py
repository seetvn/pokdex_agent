from __future__ import annotations
import json
from typing import Dict, List
from rich.console import Console
from rich.markdown import Markdown

from .prompts import SYSTEM, PLANNER_INSTRUCTION
from .tools import build_tool_registry, openai_tools_spec
from clients.llm import LLM

console = Console()

class Agent:
    def __init__(self, model: str | None = None, max_steps: int = 6, temperature: float = 0.2):
        self.llm = LLM(model=model, temperature=temperature)
        self.max_steps = max_steps
        self.registry = build_tool_registry()
        self.tools_spec = openai_tools_spec(self.registry)

    def run(self, user_query: str) -> str:
        messages: List[Dict[str, str]] = [
            {"role": "user", "content": user_query},
            {"role": "user", "content": PLANNER_INSTRUCTION},
            {"role": "system", "content": SYSTEM},
        ]
        thoughts: List[str] = []   # collect plan texts across steps

        for step in range(1, self.max_steps + 1):
            console.print(f"[bold cyan]Step {step} • Calling LLM[/bold cyan]")
            resp = self.llm.chat(messages, tools=self.tools_spec)
            tool_calls = resp.get("tool_calls", [])
            content = resp.get("content")
            if tool_calls:
                # Append the assistant message that contained the tool_calls (required by API)
                messages.append({
                    "role": "assistant",
                    "content": content or None,
                    "tool_calls": [tc for tc in tool_calls],
                })

                # Show and store the returned content (if any) for this step
                if content and content.strip():
                    thought = content.strip()
                    if not thoughts:
                        console.print(Markdown(f"** Breakdown:**\n\n{thought}"))
                    else:
                        console.print(Markdown(f"**Step {step} gained info:**\n\n{thought}"))
                    thoughts.append(thought)

                # Process each tool call in order
                for tc in tool_calls:
                    fn = tc["function"]["name"]
                    args_json = tc["function"]["arguments"]
                    console.print(f"[bold yellow]Tool call →[/bold yellow] {fn}({args_json})")

                    # Interactive clarification with the user
                    if fn == "clarify_user":
                        try:
                            question = (json.loads(args_json or "{}").get("question") or "").strip()
                        except Exception:
                            question = ""
                        if not question:
                            question = "Could you clarify your request?"

                        console.print(Markdown(f"**Agent needs clarification:** {question}"))
                        try:
                            user_answer = input("[you] ").strip()
                        except EOFError:
                            user_answer = ""

                        # Return the user's answer as the tool observation
                        observation = json.dumps({"user_answer": user_answer}, ensure_ascii=False)
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tc["id"],
                            "name": fn,
                            "content": observation,
                        })
                        # Also echo as a real user message
                        messages.append({
                            "role": "user",
                            "content": user_answer or "(no answer provided)"
                        })
                        continue

                    # Normal tool handling
                    tool = self.registry.get(fn)
                    if not tool:
                        observation = json.dumps({"error": f"Unknown tool {fn}"})
                    else:
                        try:
                            observation = tool.call(args_json)
                        except Exception as e:
                            console.print(f"[bold red]Error during tool call →[/bold red] {fn}({args_json})")
                            observation = json.dumps({"error": str(e)})

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "name": fn,
                        "content": observation,
                    })

                # Continue the loop after tools so the model can read observations
                continue

            # No tool call; either final answer (or need more guidance)
            if content and content.strip():
                console.print(Markdown("**No tool calls left, producing the output.**"))
                console.print(Markdown(f"**LLM response (step {step}):**\n\n{content.strip()}"))
                save_yes_no = input("Do you want to save the output? (y/n): ").strip().lower()
                if save_yes_no == 'y':
                    console.print(" content will be saved.")
                return 

            # If we reach here, ask the model to continue planning
            messages.append({"role": "user", "content": "Continue your plan and call the next tool."})

        # Fallback if loop ends without final answer
        return "I wasn't able to complete the research within the allotted steps. Consider increasing --max-steps."
