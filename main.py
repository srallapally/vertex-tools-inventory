from __future__ import annotations

import argparse
from pathlib import Path

from inventory.collectors.dialogflow import collect_dialogflow_agents_from_fixture
from inventory.collectors.reasoning_engines import collect_reasoning_engines_from_fixture
from inventory.config import InventoryConfig
from inventory.writers.json_writer import write_agents_json, write_manifest_json


def run(config: InventoryConfig) -> None:
    if config.flavor == "dialogflowcx":
        agents = collect_dialogflow_agents_from_fixture(config.fixture_path)
    elif config.flavor == "vertexai":
        agents = collect_reasoning_engines_from_fixture(config.fixture_path)
    else:
        raise ValueError(f"Unsupported flavor: {config.flavor}")

    write_agents_json(config.output_dir, agents)
    write_manifest_json(config.output_dir, config.flavor, len(agents))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Offline Vertex inventory job")
    parser.add_argument("--config", required=True, help="Path to inventory config json")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    config = InventoryConfig.from_file(Path(args.config))
    run(config)
