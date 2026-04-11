from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

Flavor = Literal["dialogflowcx", "vertexai"]


@dataclass(frozen=True)
class InventoryConfig:
    flavor: Flavor
    fixture_path: Path
    output_dir: Path

    @classmethod
    def from_dict(cls, payload: dict) -> "InventoryConfig":
        flavor = payload["flavor"]
        if flavor not in {"dialogflowcx", "vertexai"}:
            raise ValueError(f"Unsupported flavor: {flavor}")

        fixture_path = Path(payload["fixture_path"])
        output_dir = Path(payload["output_dir"])
        return cls(flavor=flavor, fixture_path=fixture_path, output_dir=output_dir)

    @classmethod
    def from_file(cls, path: Path) -> "InventoryConfig":
        data = json.loads(path.read_text())
        return cls.from_dict(data)
