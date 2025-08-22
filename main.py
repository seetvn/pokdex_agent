from __future__ import annotations
import argparse, os
from agent.loop import Agent

def parse_args():
    ap = argparse.ArgumentParser(description="PokeDeep – Reactive Pokédex Agent")
    ap.add_argument("question", type=str, help="User request/query")
    ap.add_argument("--model", type=str, default=os.getenv("MODEL", "gpt-4o-mini"))
    ap.add_argument("--max-steps", type=int, default=6)
    ap.add_argument("--temperature", type=float, default=0.2)
    return ap.parse_args()

def main():
    args = parse_args()
    agent = Agent(model=args.model, max_steps=args.max_steps, temperature=args.temperature)
    answer = agent.run(args.question)
    print("\n" + "="*60 + "\nFINAL ANSWER:\n" + "="*60)
    print(answer)
    print()

if __name__ == "__main__":
    main()