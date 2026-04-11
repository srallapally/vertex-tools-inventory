from __future__ import annotations

import json
from pathlib import Path

from inventory.models import NormalizedAgent
from inventory.normalize.agents import normalize_dialogflow_agent


def collect_dialogflow_agents_from_fixture(fixture_path: Path) -> list[NormalizedAgent]:
    payload = json.loads(fixture_path.read_text())
    agents = payload.get("agents", [])
    return [normalize_dialogflow_agent(agent) for agent in agents]
