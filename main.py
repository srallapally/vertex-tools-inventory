from __future__ import annotations

import argparse
import json
from pathlib import Path

from inventory.collectors.dialogflow import collect_dialogflow_agents_from_fixture
from inventory.collectors.iam import collect_iam_policies_from_fixture
from inventory.collectors.reasoning_engines import collect_reasoning_engines_from_fixture
from inventory.config import InventoryConfig
from inventory.models import NormalizedIdentityBinding
from inventory.normalize.bindings import normalize_identity_bindings
from inventory.normalize.service_accounts import normalize_service_accounts
from inventory.writers.json_writer import (
    write_agents_json,
    write_identity_bindings_json,
    write_manifest_json,
    write_service_accounts_json,
)


def run(config: InventoryConfig) -> None:
    agents = []
    resource_policies: dict[str, dict] = {}
    project_policies: dict[str, dict] = {}

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

    if config.fixtures:
        if config.iam_fixture_path is None:
            raise ValueError("iam_fixture_path is required for fixture mode")
        resource_policies, project_policies = collect_iam_policies_from_fixture(
            config.iam_fixture_path
        )

    identity_bindings = normalize_identity_bindings(
        agents=agents,
        resource_policies=resource_policies,
        project_policies=project_policies,
    )
    service_accounts = normalize_service_accounts(agents)
    warnings = _build_manifest_warnings(identity_bindings)
    flavors_included = sorted({agent.flavor for agent in agents})
    project_ids_scanned = sorted({agent.projectId for agent in agents})
    locations_scanned = sorted({agent.location for agent in agents})

    write_agents_json(config.output_dir, agents)
    write_identity_bindings_json(config.output_dir, identity_bindings)
    write_service_accounts_json(config.output_dir, service_accounts)
    write_manifest_json(
        config.output_dir,
        "fixtures" if config.fixtures else "live",
        flavors_included,
        project_ids_scanned,
        locations_scanned,
        len(agents),
        len(identity_bindings),
        len(service_accounts),
        warnings,
    )


def _build_manifest_warnings(
    identity_bindings: list[NormalizedIdentityBinding],
) -> list[str]:
    warnings: list[str] = []

    if len(identity_bindings) == 0:
        warnings.append("No identity bindings were generated.")
    if any(binding.scope == "project" for binding in identity_bindings):
        warnings.append("Project-level IAM fallback was used for one or more agents.")
    if any(binding.expanded is False for binding in identity_bindings):
        warnings.append("Group expansion is not performed in v1.")

    return warnings


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
