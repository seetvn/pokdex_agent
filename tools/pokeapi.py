from __future__ import annotations
from typing import Any, Dict, List
from clients.http import HttpClient

BASE = "https://pokeapi.co/api/v2"

#TODO: add more tools for moves, abilities, etc.
class PokeAPI:
    def __init__(self):
        self.http = HttpClient(BASE)

    # --- Core endpoints ---
    def get_pokemon(self, name: str) -> Dict[str, Any]:
        name = name.strip().lower()
        return self.http.get(f"/pokemon/{name}")

    def get_pokemon_species(self, name: str) -> Dict[str, Any]:
        name = name.strip().lower()
        return self.http.get(f"/pokemon-species/{name}")

    def get_type(self, name: str) -> Dict[str, Any]:
        return self.http.get(f"/type/{name.strip().lower()}")

    def get_move(self, name: str) -> Dict[str, Any]:
        return self.http.get(f"/move/{name.strip().lower()}")

    def list_pokemon_by_habitat(self, habitat: str) -> Dict[str, Any]:
        return self.http.get(f"/pokemon-habitat/{habitat.strip().lower()}")

    def encounters_for_pokemon(self, name: str) -> List[Dict[str, Any]]:
        name = name.strip().lower()
        return self.http.get(f"/pokemon/{name}/encounters")

    def generation(self, id_or_name: str) -> Dict[str, Any]:
        return self.http.get(f"/generation/{id_or_name}")

    def version(self, name: str) -> Dict[str, Any]:
        return self.http.get(f"/version/{name}")
    
    def get_ability(self, name: str) -> Dict[str, Any]:
        return self.http.get(f"/ability/{name.strip().lower()}")

    def get_encounter_condition(self, id_or_name: str) -> Dict[str, Any]:
        return self.http.get(f"/encounter-condition/{id_or_name}")
# Singleton
poke_api = PokeAPI()

# --- Tool handler functions (pure) ---

def tool_get_pokemon(name_or_id: str) -> Dict[str, Any]:
    data = poke_api.get_pokemon(name_or_id)
    # Summarise essential bits to keep tokens small
    moves = data.get("moves", [])
    summary = {
        "name": data.get("name"),
        "types": [t["type"]["name"] for t in data.get("types", [])],
        "base_experience": data.get("base_experience"),
        "stats": {s["stat"]["name"]: s["base_stat"] for s in data.get("stats", [])},
        "abilities": [a["ability"]["name"] for a in data.get("abilities", [])],
        "moves_count": len(data.get("moves", [])),
        "moves": [m["move"]["name"] for m in moves[:min(20,len(moves))]]  # first 20 moves
        # "encounters_url": f"{BASE}/pokemon/{data.get('name')}/encounters"
    }
    return {"summary": summary}

def tool_get_pokemon_species(name_or_id: str) -> Dict[str, Any]:
    data = poke_api.get_pokemon_species(name_or_id)
    flavor = next((e["flavor_text"] for e in data.get("flavor_text_entries", []) if e["language"]["name"] == "en"), None)
    habitat = data.get("habitat", {}).get("name")
    growth_rate = data.get("growth_rate", {}).get("name")
    is_legendary = data.get("is_legendary", False)
    is_mythical = data.get("is_mythical", False)
    capture_rate = data.get("capture_rate")
    return {
        "name": data.get("name"),
        "habitat": habitat,
        "growth_rate": growth_rate,
        "is_legendary": is_legendary,
        "is_mythical": is_mythical,
        "capture_rate": capture_rate,
        "flavor": flavor,
    }

def tool_get_type(name: str) -> Dict[str, Any]:
    data = poke_api.get_type(name)
    pokemon = [p["pokemon"]["name"] for p in data.get("pokemon", [])[:min(20,len(data.get("pokemon", [])))] ]  # first 20 Pokémon of this type
    damage_rel = data.get("damage_relations", {})
    double_to = [t["name"] for t in damage_rel.get("double_damage_to", [])]
    double_from = [t["name"] for t in damage_rel.get("double_damage_from", [])]
    half_to = [t["name"] for t in damage_rel.get("half_damage_to", [])]
    half_from = [t["name"] for t in damage_rel.get("half_damage_from", [])]
    no_to = [t["name"] for t in damage_rel.get("no_damage_to", [])]
    no_from = [t["name"] for t in damage_rel.get("no_damage_from", [])]
    return {
        "name": data.get("name"),
        "double_damage_to": double_to,
        "double_damage_from": double_from,
        "half_damage_to": half_to,
        "half_damage_from": half_from,
        "no_damage_to": no_to,
        "no_damage_from": no_from,
        "pokemon_of_type": pokemon,
    }

def tool_get_move(name: str) -> Dict[str, Any]:
    data = poke_api.get_move(name)
    return {
        "name": data.get("name"),
        "type": data.get("type", {}).get("name"),
        "power": data.get("power"),
        "pp": data.get("pp"),
        "accuracy": data.get("accuracy"),
        "damage_class": data.get("damage_class", {}).get("name"),
        "effect": next((e["short_effect"] for e in data.get("effect_entries", []) if e["language"]["name"] == "en"), None),
    }

def tool_list_pokemon_by_habitat(habitat: str) -> Dict[str, Any]:
    data = poke_api.list_pokemon_by_habitat(habitat)
    species = [s["name"] for s in data.get("pokemon_species", [])]
    return {"habitat": data.get("name"), "species": species}

def tool_encounters_for_pokemon(name: str) -> Dict[str, Any]:
    data = poke_api.encounters_for_pokemon(name)
    # Simplify
    entries = []
    for area in data:
        version_details = [v["version"]["name"] for v in area.get("version_details", [])]
        entries.append({
            "location_area": area.get("location_area", {}).get("name"),
            "versions": list(sorted(set(version_details)))
        })
    return {"name": name.lower(), "encounters": entries}

def tool_generation(id_or_name: str) -> Dict[str, Any]:
    data = poke_api.generation(id_or_name)
    return {
        "name": data.get("name"),
        "main_region": data.get("main_region", {}).get("name"),
        "version_groups": [vg["name"] for vg in data.get("version_groups", [])],
    }

def tool_version(name: str) -> Dict[str, Any]:
    data = poke_api.version(name)
    # Tie version to version_group (e.g., ruby/sapphire -> generation-iii)
    return {
        "name": data.get("name"),
        "version_group": data.get("version_group", {}).get("name"),
    }

def tool_get_ability(name: str) -> Dict[str, Any]:
    data = poke_api.get_ability(name)
    pokemon_list = data.get("pokemon", [])
    pokemon = [p["pokemon"]["name"] for p in pokemon_list[:min(20,len(pokemon_list))]]  # first 20 Pokémon with this ability
    effect = next((e["effect"] for e in data.get("effect_entries", []) if e["language"]["name"] == "en"), None)
    short_effect = next((e["short_effect"] for e in data.get("effect_entries", []) if e["language"]["name"] == "en"), None)
    return {
        "name": data.get("name"),
        "generation": data.get("generation", {}).get("name"),
        "is_main_series": data.get("is_main_series"),
        "effect": effect,
        "short_effect": short_effect,
        "pokemon_with_ability": pokemon,
    }

def tool_get_encounter_condition(id_or_name: str) -> Dict[str, Any]:
    data = poke_api.get_encounter_condition(id_or_name)
    en_name = next(
        (n.get("name") for n in data.get("names", []) if n.get("language", {}).get("name") == "en"),
        None,
    )
    values = []
    for v in data.get("values", []) or []:
        v_name = v.get("name")
        v_url = (v.get("url") or "").rstrip("/")
        v_id = v_url.split("/")[-1] if v_url else None
        values.append({"id": v_id, "name": v_name})
    return {
        "id": data.get("id"),
        "name": data.get("name"),
        "display_name": en_name or data.get("name"),
        "value_count": len(values),
        "values": values,  # e.g., [{"id": "1", "name": "morning"}, ...]
    }

