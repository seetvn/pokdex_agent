from __future__ import annotations
import json
from typing import Any, Dict, List
from rich.console import Console
from rich.markdown import Markdown
from tools.random_utls import print_observation

from .prompts import SYSTEM, PLANNER_INSTRUCTION, CONTROLLER_INSTRUCTION
from .tools import build_tool_registry
from .observations import Observation
from clients.llm import LLM
import os

console = Console()

class Agent:
    def __init__(self, model: str | None = None, max_steps: int = 6, temperature: float = 0.2, verbose: bool = False):
        self.llm = LLM(model=model, temperature=temperature)
        self.max_steps = max_steps
        self.registry = build_tool_registry()
        self.verbose = verbose
        self.current_query = None

    def _handle_call_action(
        self,
        *,
        step: int,
        tool_calls: List[Dict[str, Any]],
        messages: List[Dict[str, str]],
    ) -> None:
        """
        Execute the list of tool calls from the controller and append a single
        observations message back to `messages` for the next step.
        """
        observations: List[Observation] = []
        
        for i, tc in enumerate(tool_calls, start=1):
            fn = tc.get("tool")
            args = tc.get("args", {}) or {}
            args_json = json.dumps(args, ensure_ascii=False)
            console.print(f"[bold yellow]Tool call →[/bold yellow] {fn}({args_json})")

            obs = Observation(tool=fn, args=args, step=step)

            # Interactive path for clarify_user
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

                # Give the raw human reply as a separate user msg to help the model
                messages.append({"role": "user", "content": user_answer or "(no answer provided)"})
                continue

            # Normal tools
            tool = self.registry.get(fn)
            if not tool:
                obs.finish(error=f"Unknown tool {fn}")
            else:
                try:
                    # tool.call takes a JSON string and returns a JSON string
                    result_str = tool.call(args_json)
                    obs.finish(result=json.loads(result_str))
                except Exception as e:
                    console.print(f"[bold red]Error during tool call →[/bold red] {fn}({args_json})")
                    obs.finish(error=str(e))

            # Log if verbose
            obs.log(console, verbose=self.verbose, pretty_printer=print_observation)

            observations.append(obs)

        # Feed all observations back as a single USER message the controller can read next turn
        obs_msg = {"observations": [o.to_message_payload() for o in observations]}
        messages.append({
            "role": "user",
            "content": json.dumps(obs_msg, ensure_ascii=False)
        })

    def _handle_write_action(self, content: str) -> str:
        """
        Finalize and return the controller's report.
        """
        final_answer = (content or "").strip() or "(no report returned)"
        console.print(Markdown("**No tool calls left.**"))
        console.print(Markdown(f"**Final Report:**\n\n{final_answer}"))
        save_yes_no = input("Do you want to save the final output? (y/n): ").strip().lower()
        if save_yes_no == 'y':
            console.print(" content will be saved.")
            from datetime import datetime
            t = datetime.now().strftime("%Y%m%d_%H%M%S")
            os.makedirs("generated_reports", exist_ok=True)
            label = "_".join(self.current_query.lower().split())
            file_name = f"generated_reports/{label}_{t}.md"
            with open(file_name, "w", encoding="utf-8") as f:
                f.write(final_answer)
        return final_answer

    # ---------------------------
    # Main loop
    # ---------------------------

    def run(self, user_query: str) -> str:
        self.current_query = user_query
        messages: List[Dict[str, str]] = [
            {"role": "user", "content": user_query},
            {"role": "user", "content": PLANNER_INSTRUCTION},
            {"role": "system", "content": SYSTEM},
            {"role": "system", "content": CONTROLLER_INSTRUCTION},
        ]

        for step in range(1, self.max_steps + 1):
            console.print(f"[bold cyan]Step {step} • Calling LLM[/bold cyan]")
            resp = self.llm.chat(messages)

            action_type = resp["type"].lower().strip()
            tool_calls = resp["tool_calls"]
            content = resp["content"]

            # If the model decided to finish i.e. no more tool calls
            if action_type == "write":
                return self._handle_write_action(content=content)

            # Log controller reasoning/notes (optional)
            if content:
                console.print(Markdown(f"**Controller (step {step}):**\n\n{content}"))

            # Append the raw controller JSON so the model “remembers” its own decisions
            raw_controller = resp.get("raw_controller")
            if raw_controller:
                messages.append({"role": "assistant", "content": json.dumps(raw_controller, ensure_ascii=False)})

            # Dispatch by action
            if action_type == "call" and tool_calls:
                self._handle_call_action(step=step, tool_calls=tool_calls, messages=messages)
                # Loop so the model can read observations and decide next step
                continue


            # Unknown/empty -> nudge to continue
            messages.append({"role": "user", "content": "Continue your plan and call the next tool or finish with a report."})

        return "I wasn't able to complete the research within the allotted steps. Consider increasing --max-steps."
