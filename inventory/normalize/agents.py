from __future__ import annotations

from inventory.models import NormalizedAgent


def normalize_dialogflow_agent(raw: dict) -> NormalizedAgent:
    return NormalizedAgent(
        id=raw["agent_id"],
        flavor="dialogflowcx",
        project_id=raw["project_id"],
        location=raw["location"],
        display_name=raw["display_name"],
        resource_name=raw["resource_name"],
        source_type="dialogflowcx_agent",
    )


def normalize_reasoning_engine(raw: dict) -> NormalizedAgent:
    return NormalizedAgent(
        id=raw["engine_id"],
        flavor="vertexai",
        project_id=raw["project_id"],
        location=raw["location"],
        display_name=raw["display_name"],
        resource_name=raw["resource_name"],
        source_type="vertex_reasoning_engine",
    )
