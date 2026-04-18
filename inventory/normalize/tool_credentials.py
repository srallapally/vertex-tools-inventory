# inventory/normalize/tool_credentials.py
from __future__ import annotations

import hashlib

from inventory.models import NormalizedToolCredential


def normalize_tool_credentials(
    webhooks: list[dict],
    agent_resource_name: str,
    project_id: str,
    location: str,
) -> list[NormalizedToolCredential]:
    """
    Normalize raw Dialogflow CX webhook API responses into NormalizedToolCredential objects.
    Entries where authType resolves to NONE are excluded.

    Args:
        webhooks: raw webhook dicts from the Dialogflow CX webhooks.list API response.
        agent_resource_name: full resource name of the parent agent.
        project_id: GCP project ID.
        location: GCP region.
    """
    results = []
    for webhook in webhooks:
        credential = _normalize_one(webhook, agent_resource_name, project_id, location)
        if credential is not None:
            results.append(credential)
    return results


def derive_webhook_auth(webhook: dict) -> tuple[str, str]:
    """
    Derive (authType, credentialRef) from a raw Dialogflow CX webhook dict.
    Mirrors GoogleVertexAIClient.parseWebhookNode() auth logic exactly.

    Returns:
        (authType, credentialRef) where authType is one of:
        SERVICE_ACCOUNT, OAUTH, API_KEY, NONE.
        credentialRef is the SA email, "oauth", "api-key", or "".
    """
    generic = webhook.get("genericWebService", {})
    if generic.get("serviceAccount"):
        return "SERVICE_ACCOUNT", generic["serviceAccount"]
    if generic.get("oauthConfig"):
        return "OAUTH", "oauth"
    if generic.get("requestHeaders"):
        return "API_KEY", "api-key"
    if "serviceDirectory" in webhook:
        service = webhook["serviceDirectory"].get("service", "")
        return "SERVICE_ACCOUNT", service
    return "NONE", ""


def make_tool_key(tool_id: str) -> str:
    return tool_id.replace("/", "_")


def _normalize_one(
    webhook: dict,
    agent_resource_name: str,
    project_id: str,
    location: str,
) -> NormalizedToolCredential | None:
    tool_id = webhook.get("name", "")
    if not tool_id:
        return None

    auth_type, credential_ref = derive_webhook_auth(webhook)
    if auth_type == "NONE":
        return None

    return NormalizedToolCredential(
        id=_make_credential_id(tool_id),
        toolId=tool_id,
        toolKey=make_tool_key(tool_id),
        toolType="WEBHOOK",
        agentId=agent_resource_name,
        authType=auth_type,
        credentialRef=credential_ref,
        projectId=project_id,
        location=location,
    )


def _make_credential_id(tool_id: str) -> str:
    digest = hashlib.sha1(tool_id.encode("utf-8")).hexdigest()
    return f"tc-{digest[:16]}"