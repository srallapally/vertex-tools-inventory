from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from inventory.models import NormalizedAgent


def write_agents_json(output_dir: Path, agents: list[NormalizedAgent]) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "agents.json"
    path.write_text(json.dumps([agent.to_dict() for agent in agents], indent=2) + "\n")
    return path


def write_manifest_json(output_dir: Path, flavor: str, agent_count: int) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "manifest.json"
    payload = {
        "flavor": flavor,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "files": ["agents.json", "manifest.json"],
        "counts": {"agents": agent_count},
    }
    path.write_text(json.dumps(payload, indent=2) + "\n")
    return path
