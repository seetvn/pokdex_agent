from __future__ import annotations
from typing import Any, Callable, Dict, List
import json

from tools.pokeapi import (
    tool_get_pokemon,
    tool_get_pokemon_species,
    tool_get_type,
    tool_get_move,
    tool_list_pokemon_by_habitat,
    tool_encounters_for_pokemon,
    tool_generation,
    tool_version,
    tool_get_ability,
    tool_get_encounter_condition    
)

ToolHandler = Callable[..., Dict[str, Any]]

class Tool:
    def __init__(self, name: str, description: str, schema: Dict[str, Any], handler: ToolHandler):
        self.name = name
        self.description = description
        self.schema = schema
        self.handler = handler

    def to_openai_spec(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.schema,
            },
        }

    def call(self, arguments_json: str) -> str:
        args = json.loads(arguments_json or "{}")
        result = self.handler(**args)
        # Return as a compact JSON string
        return json.dumps(result, ensure_ascii=False)

def build_tool_registry() -> Dict[str, Tool]:
    return {
        "get_pokemon": Tool(
            name="get_pokemon",
            description="Fetch core data about a Pokemon by name (types, stats, abilities).",
            schema={
                "type": "object",
                "properties": {"name": {"type": "string"}},
                "required": ["name"],
            },
            handler=tool_get_pokemon,
        ),
        "get_pokemon_species": Tool(
            name="get_pokemon_species",
            description="Fetch  additional data about Pokemon: Pokemon species info (habitat, growth rate, legendary/mythical flags).",
            schema={
                "type": "object",
                "properties": {"name": {"type": "string"}},
                "required": ["name"],
            },
            handler=tool_get_pokemon_species,
        ),
        "get_type": Tool(
            name="get_type",
            description="Fetch type chart relations for a given Pokémon type name.",
            schema={
                "type": "object",
                "properties": {"name": {"type": "string"}},
                "required": ["name"],
            },
            handler=tool_get_type,
        ),
        "get_move": Tool(
            name="get_move",
            description="Fetch move details by name.",
            schema={
                "type": "object",
                "properties": {"name": {"type": "string"}},
                "required": ["name"],
            },
            handler=tool_get_move,
        ),
        "list_pokemon_by_habitat": Tool(
            name="list_pokemon_by_habitat",
            description="List Pokémon species that belong to a given habitat (e.g., sea, cave, forest).",
            schema={
                "type": "object",
                "properties": {"habitat": {"type": "string"}},
                "required": ["habitat"],
            },
            handler=tool_list_pokemon_by_habitat,
        ),
        "encounters_for_pokemon": Tool(
            name="encounters_for_pokemon",
            description="List encounter locations and version availability for a Pokémon by name.",
            schema={
                "type": "object",
                "properties": {"name": {"type": "string"}},
                "required": ["name"],
            },
            handler=tool_encounters_for_pokemon,
        ),
        "generation": Tool(
            name="generation",
            description="Fetch generation details and supported version groups.",
            schema={
                "type": "object",
                "properties": {"id_or_name": {"type": "string"}},
                "required": ["id_or_name"],
            },
            handler=tool_generation,
        ),
        "version": Tool(
            name="version",
            description="Fetch version details and linked version group (e.g., ruby -> generation-iii).",
            schema={
                "type": "object",
                "properties": {"name": {"type": "string"}},
                "required": ["name"],
            },
            handler=tool_version,
        ),
        "get_ability": Tool(
            name="get_ability",
            description="Fetch a Pokémon ability (effect, short effect, generation, main-series flag, and which Pokémon can have it).",
            schema={
                "type": "object",
                "properties": {"name": {"type": "string"}},
                "required": ["name"],
            },
            handler=tool_get_ability,
        ),
        "clarify_user": Tool(
            name="clarify_user",
            description="Ask the user for clarification on their request. Use it to correct misunderstandings or fill in missing context.",
            schema={
                "type": "object",
                "properties": {"question": {"type": "string"}},
                "required": ["question"],
            },
            # If your loop handles this interactively, the handler won't be used.
            handler=lambda question: {"response": f"Please clarify: {question}"},
        ),
        "get_encounter_condition": Tool(
            name="get_encounter_condition",
            description="Fetch an encounter condition (e.g., 'time') and list its possible values.",
            schema={
                "type": "object",
                "properties": {"id_or_name": {"type": "string"}},
                "required": ["id_or_name"],
            },
            handler=tool_get_encounter_condition,
        ),
    }

# unused for now, but could be useful if switching to native tool-calling
def openai_tools_spec(tool_registry: Dict[str, Tool]) -> List[Dict[str, Any]]:
    return [t.to_openai_spec() for t in tool_registry.values()]

#TODO: add more tools for evolution, items 