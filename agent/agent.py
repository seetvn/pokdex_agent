from __future__ import annotations
import json
from typing import Dict, List
from rich.console import Console
from rich.markdown import Markdown
from tools.random_utls import print_observation 

from .prompts import SYSTEM, PLANNER_INSTRUCTION, CONTROLLER_INSTRUCTION
from .tools import build_tool_registry
from .observations import Observation
from clients.llm import LLM

console = Console()

class Agent:
    def __init__(self, model: str | None = None, max_steps: int = 6, temperature: float = 0.2, verbose: bool = False):
        self.llm = LLM(model=model, temperature=temperature)
        self.max_steps = max_steps
        self.registry = build_tool_registry()
        self.verbose = verbose

    def run(self, user_query: str) -> str:
        messages: List[Dict[str, str]] = [
            {"role": "user", "content": user_query},
            {"role": "user", "content": PLANNER_INSTRUCTION},
            {"role": "system", "content": SYSTEM},
            {"role": "system", "content": CONTROLLER_INSTRUCTION},
        ]

        for step in range(1, self.max_steps + 1):
            console.print(f"[bold cyan]Step {step} • Calling LLM[/bold cyan]")
            resp = self.llm.chat(messages)
            action_type = (resp.get("type") or "").lower().strip()
            tool_calls = resp.get("tool_calls", []) or []
            content = resp.get("content") or ""

            if content:
                console.print(Markdown(f"**Controller (step {step}):**\n\n{content}"))

            raw_controller = resp.get("raw_controller")
            if raw_controller:
                messages.append({"role": "assistant", "content": json.dumps(raw_controller, ensure_ascii=False)})

            # ---- ACTION: CALL TOOLS ----
            if action_type == "call" and tool_calls:
                observations: List[Observation] = []
                for i, tc in enumerate(tool_calls, start=1):
                    fn = tc.get("tool")
                    args = tc.get("args") or {}
                    args_json = json.dumps(args, ensure_ascii=False)
                    console.print(f"[bold yellow]Tool call →[/bold yellow] {fn}({args_json})")

                    obs = Observation(tool=fn, args=args, step=step)

                    # Special interactive path for clarify_user
                    if fn == "clarify_user":
                        question = (args.get("question") or "").strip() or "Could you clarify your request?"
                        console.print(Markdown(f"**Agent needs clarification:** {question}"))
                        try:
                            user_answer = input("[you] ").strip()
                        except EOFError:
                            user_answer = ""
                        obs.finish(result={"user_answer": user_answer})
                        observations.append(obs)

                        # Log if verbose
                        obs.log(console, verbose=self.verbose, pretty_printer=print_observation)

                        # Give the raw human reply as a separate user msg
                        messages.append({"role": "user", "content": user_answer or "(no answer provided)"})
                        continue

                    # Normal tools
                    tool = self.registry.get(fn)
                    if not tool:
                        obs.finish(error=f"Unknown tool {fn}")
                    else:
                        try:
                            result_str = tool.call(args_json)
                            obs.finish(result=json.loads(result_str))
                        except Exception as e:
                            console.print(f"[bold red]Error during tool call →[/bold red] {fn}({args_json})")
                            obs.finish(error=str(e))

                    # Log if verbose
                    obs.log(console, verbose=self.verbose, pretty_printer=print_observation)

                    observations.append(obs)

                # Feed all observations back as a single USER message
                obs_msg = {"observations": [o.to_message_payload() for o in observations]}
                messages.append({
                    "role": "user",
                    "content": json.dumps(obs_msg, ensure_ascii=False)
                })
                continue

            # ---- ACTION: WRITE (FINAL ANSWER) ----
            if action_type == "write":
                final_answer = content.strip() or "(no report returned)"
                console.print(Markdown("**No tool calls left.**"))
                save_yes_no = input("Do you want to save the final output? (y/n): ").strip().lower()
                if save_yes_no == 'y':
                    console.print(" content will be saved.")
                return final_answer

            # ---- UNKNOWN / EMPTY → ask it to continue ----
            messages.append({"role": "user", "content": "Continue your plan and call the next tool or finish with a report."})

        return "I wasn't able to complete the research within the allotted steps. Consider increasing --max-steps."
