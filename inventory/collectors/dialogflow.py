from __future__ import annotations

import json
import subprocess
from pathlib import Path

from inventory.config import InventoryConfig
from inventory.models import NormalizedAgent
from inventory.normalize.agents import normalize_dialogflow_agent


def collect_dialogflow_agents_from_fixture(fixture_path: Path) -> list[NormalizedAgent]:
    payload = json.loads(fixture_path.read_text())
    agents = payload.get("agents", [])
    return [normalize_dialogflow_agent(agent) for agent in agents]


def collect_dialogflow_agents_live(config: InventoryConfig) -> list[NormalizedAgent]:
    agents: list[NormalizedAgent] = []

    for project_id in config.project_ids:
        for location in config.locations:
            payload = _run_gcloud_json(
                [
                    "gcloud",
                    "dialogflow",
                    "cx",
                    "agents",
                    "list",
                    f"--project={project_id}",
                    f"--location={location}",
                    "--format=json",
                ]
            )
            for agent in payload if isinstance(payload, list) else []:
                resource_name = agent.get("name")
                if not resource_name:
                    continue
                agents.append(
                    normalize_dialogflow_agent(
                        {
                            "agent_id": resource_name.rsplit("/", 1)[-1],
                            "project_id": project_id,
                            "location": location,
                            "display_name": agent.get("displayName", ""),
                            "resource_name": resource_name,
                            "runtime_identity": None,
                        }
                    )
                )

    return agents


def _run_gcloud_json(command: list[str]) -> list[dict] | dict:
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return []

    if completed.returncode != 0 or not completed.stdout.strip():
        return []

    try:
        parsed = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return []

    if isinstance(parsed, (list, dict)):
        return parsed
    return []
