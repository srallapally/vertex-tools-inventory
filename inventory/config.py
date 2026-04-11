from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

Flavor = Literal["dialogflowcx", "vertexai", "both"]


@dataclass(frozen=True)
class InventoryConfig:
    flavor: Flavor
    fixture_path: Path
    output_dir: Path
    fixtures: bool = True

    @classmethod
    def from_dict(cls, payload: dict) -> "InventoryConfig":
        flavor = payload["flavor"]
        if flavor not in {"dialogflowcx", "vertexai", "both"}:
            raise ValueError(f"Unsupported flavor: {flavor}")

        fixture_path = Path(payload["fixture_path"])
        output_dir = Path(payload["output_dir"])
        fixtures = payload.get("fixtures", True)
        return cls(
            flavor=flavor,
            fixture_path=fixture_path,
            output_dir=output_dir,
            fixtures=fixtures,
        )

    @classmethod
    def from_file(cls, path: Path) -> "InventoryConfig":
        data = json.loads(path.read_text())
        return cls.from_dict(data)
