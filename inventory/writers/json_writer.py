from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from inventory.models import (
    NormalizedAgent,
    NormalizedIdentityBinding,
    NormalizedServiceAccount,
)


def write_agents_json(output_dir: Path, agents: list[NormalizedAgent]) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "agents.json"
    path.write_text(json.dumps([agent.to_dict() for agent in agents], indent=2) + "\n")
    return path


def write_identity_bindings_json(
    output_dir: Path, bindings: list[NormalizedIdentityBinding]
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "identity-bindings.json"
    path.write_text(json.dumps([binding.to_dict() for binding in bindings], indent=2) + "\n")
    return path


def write_service_accounts_json(
    output_dir: Path, service_accounts: list[NormalizedServiceAccount]
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "service-accounts.json"
    path.write_text(
        json.dumps([service_account.to_dict() for service_account in service_accounts], indent=2)
        + "\n"
    )
    return path


def write_manifest_json(
    output_dir: Path,
    collection_mode: str,
    flavors_included: list[str],
    project_ids_scanned: list[str],
    locations_scanned: list[str],
    agent_count: int,
    identity_binding_count: int,
    service_account_count: int,
    warnings: list[str],
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "manifest.json"
    payload = {
        "generatedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "schemaVersion": "1.0",
        "platform": "GOOGLE_VERTEX_AI",
        "collectionMode": collection_mode,
        "flavorsIncluded": flavors_included,
        "projectIdsScanned": project_ids_scanned,
        "locationsScanned": locations_scanned,
        "agentCount": agent_count,
        "identityBindingCount": identity_binding_count,
        "serviceAccountCount": service_account_count,
        "artifacts": {
            "agents": {"file": "agents.json", "count": agent_count},
            "identityBindings": {
                "file": "identity-bindings.json",
                "count": identity_binding_count,
            },
            "serviceAccounts": {
                "file": "service-accounts.json",
                "count": service_account_count,
            },
        },
        "warnings": warnings,
    }
    path.write_text(json.dumps(payload, indent=2) + "\n")
    return path
