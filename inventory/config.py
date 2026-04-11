from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

Flavor = Literal["dialogflowcx", "vertexai", "both"]


@dataclass(frozen=True)
class InventoryConfig:
    flavor: Flavor
    dialogflow_fixture_path: Path | None
    vertex_fixture_path: Path | None
    iam_fixture_path: Path | None
    output_dir: Path
    fixtures: bool = True

    @classmethod
    def from_dict(cls, payload: dict) -> "InventoryConfig":
        flavor = payload["flavor"]
        if flavor not in {"dialogflowcx", "vertexai", "both"}:
            raise ValueError(f"Unsupported flavor: {flavor}")

        output_dir = Path(payload["output_dir"])
        fixtures = payload.get("fixtures", True)
        dialogflow_fixture_path = (
            Path(payload["dialogflow_fixture_path"])
            if payload.get("dialogflow_fixture_path")
            else None
        )
        vertex_fixture_path = (
            Path(payload["vertex_fixture_path"])
            if payload.get("vertex_fixture_path")
            else None
        )
        iam_fixture_path = (
            Path(payload["iam_fixture_path"]) if payload.get("iam_fixture_path") else None
        )

        if fixtures:
            if flavor in {"dialogflowcx", "both"}:
                if dialogflow_fixture_path is None:
                    raise ValueError(
                        "dialogflow_fixture_path is required for fixture mode "
                        "with flavor dialogflowcx or both"
                    )
                if not dialogflow_fixture_path.exists():
                    raise ValueError(
                        f"dialogflow_fixture_path does not exist: "
                        f"{dialogflow_fixture_path}"
                    )
                if not dialogflow_fixture_path.is_file():
                    raise ValueError(
                        f"dialogflow_fixture_path must be a file, not a directory: "
                        f"{dialogflow_fixture_path}"
                    )

            if flavor in {"vertexai", "both"}:
                if vertex_fixture_path is None:
                    raise ValueError(
                        "vertex_fixture_path is required for fixture mode "
                        "with flavor vertexai or both"
                    )
                if not vertex_fixture_path.exists():
                    raise ValueError(
                        f"vertex_fixture_path does not exist: {vertex_fixture_path}"
                    )
                if not vertex_fixture_path.is_file():
                    raise ValueError(
                        f"vertex_fixture_path must be a file, not a directory: "
                        f"{vertex_fixture_path}"
                    )

            if iam_fixture_path is None:
                raise ValueError(
                    "iam_fixture_path is required for fixture mode when generating identity bindings"
                )
            if not iam_fixture_path.exists():
                raise ValueError(f"iam_fixture_path does not exist: {iam_fixture_path}")
            if not iam_fixture_path.is_file():
                raise ValueError(
                    f"iam_fixture_path must be a file, not a directory: {iam_fixture_path}"
                )

        return cls(
            flavor=flavor,
            dialogflow_fixture_path=dialogflow_fixture_path,
            vertex_fixture_path=vertex_fixture_path,
            iam_fixture_path=iam_fixture_path,
            output_dir=output_dir,
            fixtures=fixtures,
        )

    @classmethod
    def from_file(cls, path: Path) -> "InventoryConfig":
        data = json.loads(path.read_text())
        return cls.from_dict(data)
