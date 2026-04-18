# inventory/normalize/service_accounts.py
from __future__ import annotations

from inventory.models import NormalizedAgent, NormalizedServiceAccount


def normalize_service_accounts(
    agents: list[NormalizedAgent],
    enrichment: dict[str, dict] | None = None,
) -> list[NormalizedServiceAccount]:
    deduped: dict[str, NormalizedServiceAccount] = {}

    for agent in agents:
        runtime_identity = agent.runtimeIdentity
        if runtime_identity is None:
            continue

        normalized_runtime_identity = _normalize_runtime_identity(runtime_identity)
        email = _email_from_runtime_identity(normalized_runtime_identity)
        service_account_id = f"projects/{agent.projectId}/serviceAccounts/{email}"

        existing = deduped.get(service_account_id)
        if existing is None:
            deduped[service_account_id] = NormalizedServiceAccount(
                id=service_account_id,
                platform=agent.platform,
                email=email,
                projectId=agent.projectId,
                linkedAgentIds=[agent.id],
            )
            continue

        if agent.id in existing.linkedAgentIds:
            continue

        deduped[service_account_id] = NormalizedServiceAccount(
            id=existing.id,
            platform=existing.platform,
            email=existing.email,
            projectId=existing.projectId,
            linkedAgentIds=[*existing.linkedAgentIds, agent.id],
        )

    # OPENICF-4009: apply enrichment from IAM SA GET + keys LIST
    if not enrichment:
        return list(deduped.values())

    enriched: list[NormalizedServiceAccount] = []
    for sa in deduped.values():
        data = enrichment.get(sa.id)
        if data is None:
            enriched.append(sa)
            continue
        enriched.append(NormalizedServiceAccount(
            id=sa.id,
            platform=sa.platform,
            email=sa.email,
            projectId=sa.projectId,
            linkedAgentIds=sa.linkedAgentIds,
            name=data.get("name"),
            displayName=data.get("displayName"),
            description=data.get("description"),
            uniqueId=data.get("uniqueId"),
            oauth2ClientId=data.get("oauth2ClientId"),
            disabled=data.get("disabled", False),
            createTime=data.get("createTime"),
            keysJson=data.get("keysJson"),
            keyCount=data.get("keyCount", 0),
        ))
    return enriched


def _normalize_runtime_identity(runtime_identity: str) -> str:
    if runtime_identity.startswith("serviceAccount:"):
        return runtime_identity
    return f"serviceAccount:{runtime_identity}"


def _email_from_runtime_identity(runtime_identity: str) -> str:
    return runtime_identity.split("serviceAccount:", 1)[1]