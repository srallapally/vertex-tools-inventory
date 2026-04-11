from __future__ import annotations

from inventory.models import NormalizedAgent


def normalize_dialogflow_agent(raw: dict) -> NormalizedAgent:
    return NormalizedAgent(
        id=raw["agent_id"],
        platform="GOOGLE_VERTEX_AI",
        flavor="dialogflowcx",
        projectId=raw["project_id"],
        location=raw["location"],
        displayName=raw["display_name"],
        resourceName=raw["resource_name"],
        sourceType="dialogflowcx_agent",
        runtimeIdentity=raw.get("runtime_identity"),
        toolIds=[],
        knowledgeBaseIds=[],
        guardrailId=None,
    )


def normalize_reasoning_engine(raw: dict) -> NormalizedAgent:
    return NormalizedAgent(
        id=raw["engine_id"],
        platform="GOOGLE_VERTEX_AI",
        flavor="vertexai",
        projectId=raw["project_id"],
        location=raw["location"],
        displayName=raw["display_name"],
        resourceName=raw["resource_name"],
        sourceType="vertex_reasoning_engine",
        runtimeIdentity=raw.get("service_account_identity", raw.get("service_account")),
        toolIds=[],
        knowledgeBaseIds=[],
        guardrailId=None,
    )
