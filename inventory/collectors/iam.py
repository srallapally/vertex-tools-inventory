from __future__ import annotations

import json
import subprocess
from pathlib import Path

from inventory.models import NormalizedAgent

PolicyMap = dict[str, dict]


def collect_iam_policies_from_fixture(fixture_path: Path) -> tuple[PolicyMap, PolicyMap]:
    payload = json.loads(fixture_path.read_text())
    resource_policies = payload.get("resource_iam_policies", {})
    project_policies = payload.get("project_iam_policies", {})
    return resource_policies, project_policies


def collect_iam_policies_live(agents: list[NormalizedAgent]) -> tuple[PolicyMap, PolicyMap]:
    resource_policies: PolicyMap = {}
    project_policies: PolicyMap = {}

    for agent in agents:
        resource_policy = _collect_resource_policy(agent)
        if resource_policy:
            resource_policies[agent.resourceName] = resource_policy
            continue

        project_key = f"projects/{agent.projectId}"
        if project_key in project_policies:
            continue

        project_policy = _run_gcloud_json(
            [
                "gcloud",
                "projects",
                "get-iam-policy",
                agent.projectId,
                "--format=json",
            ]
        )
        if project_policy:
            project_policies[project_key] = project_policy

    return resource_policies, project_policies


def _collect_resource_policy(agent: NormalizedAgent) -> dict:
    if agent.flavor == "dialogflowcx":
        return _run_gcloud_json(
            [
                "gcloud",
                "dialogflow",
                "cx",
                "agents",
                "get-iam-policy",
                agent.id,
                f"--project={agent.projectId}",
                f"--location={agent.location}",
                "--format=json",
            ]
        )

    return _run_gcloud_json(
        [
            "gcloud",
            "beta",
            "ai",
            "reasoning-engines",
            "get-iam-policy",
            agent.id,
            f"--project={agent.projectId}",
            f"--region={agent.location}",
            "--format=json",
        ]
    )


def _run_gcloud_json(command: list[str]) -> dict:
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return {}

    if completed.returncode != 0 or not completed.stdout.strip():
        return {}

    try:
        parsed = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return {}

    if isinstance(parsed, dict):
        return parsed
    return {}
