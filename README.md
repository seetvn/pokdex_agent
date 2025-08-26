
---

## Core Idea

The agent doesn’t plan everything at once. Instead, it:
1. Reads the user’s question.
2. Decides what information is missing.
3. Calls the right function (e.g., get Pokémon data, fetch a type, get ability).
4. Observes the response.
5. Uses that new info to decide the *next* function call.
6. Repeats until it can confidently finish with an answer.

---

## Example of Available Functions

- `get_pokemon_data(name)` → calls `/pokemon/{name}` for stats, types, moves, encounters.
- `get_game_generation_info(name)` → calls `/generation/{name}` to see what species and version groups belong to a generation.
- `get_pokedex(name)` → calls `/pokedex/{name}` for the list of Pokémon in that dex.

Each function wraps a PokéAPI endpoint. The agent doesn’t hit everything at once — it chooses based on what’s needed.

---

## Example Flow

**Question:** “Tell me about Pikachu.”

**Step 1 — Controller**  
The agent decides to start with core data.  
Tool call → `get_pokemon_data("pikachu")`  
→ Observation: Pikachu’s base stats, types, abilities, base XP.

**Step 2 — Controller**  
The agent realises it also needs training ease and encounters.  
Tool call → `get_pokemon_species("pikachu")`  
Tool call → `encounters_for_pokemon("pikachu")`  
→ First attempt fails due to wrong args.

**Step 3 — Controller**  
The agent corrects itself and tries another approach.
Tool call → `list_pokemon_by_habitat("forest")`  
→ Observation: Pikachu’s habitat and neighbours.

**Step 4 — Controller**  
No more tool calls needed. The agent assembles the report:

- **Type:** Electric  
- **Base Stats:** HP 35, Attack 55, Defense 40, Sp. Atk 50, Sp. Def 50, Speed 90  
- **Abilities:** Static, Lightning Rod  
- **Base Experience:** 112  
- **Growth Rate:** Medium  
- **Capture Rate:** 190 (easy to catch)  
- **Habitat:** Forest  
- **Notable Moves:** Thunder Shock, Thunderbolt, Thunder Wave, Surf (event)

**Final Answer**  
Pikachu is a versatile Electric-type with good speed and accessible moves. Its capture rate and growth rate make it beginner-friendly and effective in playthroughs.

---

## Summary

The agent is a **decision + action loop** over a set of PokéAPI functions.  
It builds answers step by step, rather than pulling everything blindly.  
This makes it efficient, transparent, and easy to grow.
"""
## How to run
Use the command ```python run_agent.py  --max-steps 30 ``` to run the agent, after setting the ```AI_API_KEY``` with .env

You can add the ```verbose``` flag to see the observations afer each step.

You can also change the model via ```model``` flag.
