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
    flavor: str,
    agent_count: int,
    identity_binding_count: int,
    service_account_count: int,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "manifest.json"
    payload = {
        "flavor": flavor,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "files": [
            "agents.json",
            "identity-bindings.json",
            "service-accounts.json",
            "manifest.json",
        ],
        "counts": {
            "agents": agent_count,
            "identity_bindings": identity_binding_count,
            "service_accounts": service_account_count,
        },
    }
    path.write_text(json.dumps(payload, indent=2) + "\n")
    return path
