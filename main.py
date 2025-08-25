from __future__ import annotations
import argparse, os
from agent.agent import Agent

def parse_args():
    ap = argparse.ArgumentParser(description="PokeDeep – Reactive Pokédex Agent")
    ap.add_argument("--model", type=str, default=os.getenv("MODEL", "gpt-4o-mini"))
    ap.add_argument("--max-steps", type=int, default=6)
    ap.add_argument("--temperature", type=float, default=0.4)
    ap.add_argument("--verbose", action="store_true", help="Show detailed tool call results")
    return ap.parse_args()

#TODO: add back query argument for one-off queries
def main():
    args = parse_args()
    agent = Agent(model=args.model, max_steps=args.max_steps, temperature=args.temperature,verbose=args.verbose)
    while True:
        question = input("\nWhat would you like to know? (or 'exit' to quit): \n").strip()
        if question .lower() in ("exit", "quit"):
            print("Goodbye!")
            break
        agent.run(question)

if __name__ == "__main__":
    main()