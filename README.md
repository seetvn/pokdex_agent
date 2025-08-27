
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

- `tool_get_pokemon(name)` → calls `/pokemon/{name}` for stats, types, moves, encounters.
- `tool_get_move(name)` for details about a move: type, power etc..

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
## How to run
First set the ```AI_API_KEY``` and the ```MODEL``` as needed within ```.env```, a template file is provided.
Use the command ```python run_agent.py  --max-steps 30 ``` to run the agent.

You can add the ```verbose``` flag to see the observations afer each step.

You can also change the model via ```model``` flag.

## Overview of the development process
**First iteration** : Initially, I used function calling by passing the tools directly into the LLM via the ```tools``` param but I could not get it to output its reasoning for making those tool calls where each response would either only have some output content and none of the tool calls or vice versa.
**Second iteration** : I decided to no longer use tool calls but to have the output content be in a json format listing all the tool calls it will make and the reasoning for doing so. The approach worked well and the model would try different tools it had access to if it the curent tool call it made did not work as intended or at all (API error).

## Next steps
A bottleneck that was observed was during API calls at each call step: I believe this could be made faster by making the API calls asynchronous rather than having them be sequential.
