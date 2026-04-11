from __future__ import annotations

import argparse
import json
from pathlib import Path

from inventory.collectors.dialogflow import collect_dialogflow_agents_from_fixture
from inventory.collectors.reasoning_engines import collect_reasoning_engines_from_fixture
from inventory.config import InventoryConfig
from inventory.writers.json_writer import write_agents_json, write_manifest_json


def run(config: InventoryConfig) -> None:
    if config.flavor == "dialogflowcx":
        if config.dialogflow_fixture_path is None:
            raise ValueError("dialogflow_fixture_path is required for dialogflowcx")
        agents = collect_dialogflow_agents_from_fixture(config.dialogflow_fixture_path)
    elif config.flavor == "vertexai":
        if config.vertex_fixture_path is None:
            raise ValueError("vertex_fixture_path is required for vertexai")
        agents = collect_reasoning_engines_from_fixture(config.vertex_fixture_path)
    elif config.flavor == "both":
        if config.dialogflow_fixture_path is None or config.vertex_fixture_path is None:
            raise ValueError(
                "dialogflow_fixture_path and vertex_fixture_path are required for both"
            )
        agents = collect_dialogflow_agents_from_fixture(config.dialogflow_fixture_path)
        agents.extend(collect_reasoning_engines_from_fixture(config.vertex_fixture_path))
    else:
        raise ValueError(f"Unsupported flavor: {config.flavor}")

    write_agents_json(config.output_dir, agents)
    write_manifest_json(config.output_dir, config.flavor, len(agents))


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Offline Vertex inventory job")
    parser.add_argument("--config", required=True, help="Path to inventory config json")
    parser.add_argument(
        "--flavor",
        choices=["dialogflowcx", "vertexai", "both"],
        help="Inventory flavor to collect",
    )
    parser.add_argument("--output-dir", help="Artifact output directory")
    parser.add_argument(
        "--fixtures",
        action="store_true",
        default=None,
        help="Use fixture-based collectors",
    )
    return parser.parse_args(argv)


def load_config(args: argparse.Namespace) -> InventoryConfig:
    config_payload = json.loads(Path(args.config).read_text())

    overrides: dict[str, object] = dict(config_payload)
    if args.flavor is not None:
        overrides["flavor"] = args.flavor
    if args.output_dir is not None:
        overrides["output_dir"] = args.output_dir
    if args.fixtures is not None:
        overrides["fixtures"] = args.fixtures

    return InventoryConfig.from_dict(overrides)


if __name__ == "__main__":
    args = parse_args()
    config = load_config(args)
    run(config)
