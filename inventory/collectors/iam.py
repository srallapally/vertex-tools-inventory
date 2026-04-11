from __future__ import annotations

import json
from pathlib import Path


PolicyMap = dict[str, dict]


def collect_iam_policies_from_fixture(fixture_path: Path) -> tuple[PolicyMap, PolicyMap]:
    payload = json.loads(fixture_path.read_text())
    resource_policies = payload.get("resource_iam_policies", {})
    project_policies = payload.get("project_iam_policies", {})
    return resource_policies, project_policies
