from __future__ import annotations

import json
from pathlib import Path

from inventory.models import NormalizedAgent
from inventory.normalize.agents import normalize_reasoning_engine


def collect_reasoning_engines_from_fixture(fixture_path: Path) -> list[NormalizedAgent]:
    payload = json.loads(fixture_path.read_text())
    engines = payload.get("reasoning_engines", [])
    return [normalize_reasoning_engine(engine) for engine in engines]
