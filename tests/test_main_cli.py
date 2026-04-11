from pathlib import Path
import json

import pytest

from main import load_config, parse_args, run


def _write_config(path: Path) -> None:
    path.write_text(
        (
            '{"flavor":"dialogflowcx",'
            '"dialogflow_fixture_path":"tests/fixtures/dialogflow_agent.json",'
            '"vertex_fixture_path":"tests/fixtures/reasoning_engine.json",'
            '"iam_fixture_path":"tests/fixtures/iam_policies.json",'
            '"output_dir":"build/artifacts",'
            '"fixtures":false}'
        )
    )


def test_config_only_invocation_uses_file_values(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    _write_config(config_path)

    args = parse_args(["--config", str(config_path)])
    config = load_config(args)

    assert config.flavor == "dialogflowcx"
    assert config.output_dir == Path("build/artifacts")
    assert config.fixtures is False
    assert config.bucket_name is None
    assert config.bucket_prefix == ""
    assert config.write_latest is False


def test_config_reads_gcs_batch_fields(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    config_path.write_text(
        (
            '{"flavor":"dialogflowcx",'
            '"dialogflow_fixture_path":"tests/fixtures/dialogflow_agent.json",'
            '"vertex_fixture_path":"tests/fixtures/reasoning_engine.json",'
            '"iam_fixture_path":"tests/fixtures/iam_policies.json",'
            '"output_dir":"build/artifacts",'
            '"bucketName":"vertex-tools-artifacts",'
            '"bucketPrefix":"inventory/prod",'
            '"writeLatest":true,'
            '"fixtures":false}'
        )
    )

    args = parse_args(["--config", str(config_path)])
    config = load_config(args)

    assert config.bucket_name == "vertex-tools-artifacts"
    assert config.bucket_prefix == "inventory/prod"
    assert config.write_latest is True


def test_config_plus_flavor_overrides_file_value(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    _write_config(config_path)

    args = parse_args(["--config", str(config_path), "--flavor", "vertexai"])
    config = load_config(args)

    assert config.flavor == "vertexai"


def test_config_plus_output_dir_overrides_file_value(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    _write_config(config_path)

    args = parse_args(["--config", str(config_path), "--output-dir", "custom/out"])
    config = load_config(args)

    assert config.output_dir == Path("custom/out")


def test_config_plus_fixtures_overrides_file_value(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    _write_config(config_path)

    args = parse_args(["--config", str(config_path), "--fixtures"])
    config = load_config(args)

    assert config.fixtures is True


def test_dialogflow_flavor_accepts_valid_dialogflow_fixture_file(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    config_path.write_text(
        (
            '{"flavor":"dialogflowcx",'
            '"dialogflow_fixture_path":"tests/fixtures/dialogflow_agent.json",'
            '"iam_fixture_path":"tests/fixtures/iam_policies.json",'
            '"output_dir":"build/artifacts",'
            '"fixtures":true}'
        )
    )

    args = parse_args(["--config", str(config_path)])
    config = load_config(args)
    assert config.dialogflow_fixture_path == Path("tests/fixtures/dialogflow_agent.json")


def test_vertex_flavor_accepts_valid_vertex_fixture_file(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    config_path.write_text(
        (
            '{"flavor":"vertexai",'
            '"vertex_fixture_path":"tests/fixtures/reasoning_engine.json",'
            '"iam_fixture_path":"tests/fixtures/iam_policies.json",'
            '"output_dir":"build/artifacts",'
            '"fixtures":true}'
        )
    )

    args = parse_args(["--config", str(config_path)])
    config = load_config(args)
    assert config.vertex_fixture_path == Path("tests/fixtures/reasoning_engine.json")


def test_dialogflow_fixture_directory_raises_value_error(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    config_path.write_text(
        (
            '{"flavor":"dialogflowcx",'
            '"dialogflow_fixture_path":"tests/fixtures",'
            '"iam_fixture_path":"tests/fixtures/iam_policies.json",'
            '"output_dir":"build/artifacts",'
            '"fixtures":true}'
        )
    )

    args = parse_args(["--config", str(config_path)])
    with pytest.raises(ValueError, match="must be a file"):
        load_config(args)


def test_vertex_fixture_missing_file_raises_value_error(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    config_path.write_text(
        (
            '{"flavor":"vertexai",'
            '"vertex_fixture_path":"tests/fixtures/missing.json",'
            '"iam_fixture_path":"tests/fixtures/iam_policies.json",'
            '"output_dir":"build/artifacts",'
            '"fixtures":true}'
        )
    )

    args = parse_args(["--config", str(config_path)])
    with pytest.raises(ValueError, match="does not exist"):
        load_config(args)


def test_both_flavor_requires_both_fixture_files(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    config_path.write_text(
        (
            '{"flavor":"both",'
            '"dialogflow_fixture_path":"tests/fixtures/dialogflow_agent.json",'
            '"vertex_fixture_path":"tests/fixtures/reasoning_engine.json",'
            '"iam_fixture_path":"tests/fixtures/iam_policies.json",'
            '"output_dir":"build/artifacts",'
            '"fixtures":true}'
        )
    )

    args = parse_args(["--config", str(config_path)])
    config = load_config(args)
    assert config.dialogflow_fixture_path == Path("tests/fixtures/dialogflow_agent.json")
    assert config.vertex_fixture_path == Path("tests/fixtures/reasoning_engine.json")


def test_cli_overrides_apply_before_validation(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    config_path.write_text(
        (
            '{"flavor":"dialogflowcx",'
            '"vertex_fixture_path":"tests/fixtures/reasoning_engine.json",'
            '"iam_fixture_path":"tests/fixtures/iam_policies.json",'
            '"output_dir":"build/artifacts",'
            '"fixtures":true}'
        )
    )

    args = parse_args(["--config", str(config_path), "--flavor", "vertexai"])
    config = load_config(args)
    assert config.flavor == "vertexai"


def test_fixture_mode_run_writes_agents_json_for_both(tmp_path: Path) -> None:
    output_dir = tmp_path / "out"
    config_path = tmp_path / "config.json"
    config_path.write_text(
        (
            '{"flavor":"both",'
            '"dialogflow_fixture_path":"tests/fixtures/dialogflow_agent.json",'
            '"vertex_fixture_path":"tests/fixtures/reasoning_engine.json",'
            '"iam_fixture_path":"tests/fixtures/iam_policies.json",'
            f'"output_dir":"{output_dir}",'
            '"fixtures":true}'
        )
    )

    args = parse_args(["--config", str(config_path), "--fixtures"])
    config = load_config(args)
    run(config)

    assert (output_dir / "agents.json").exists()
    assert (output_dir / "identity-bindings.json").exists()
    assert (output_dir / "service-accounts.json").exists()
    identity_bindings = json.loads((output_dir / "identity-bindings.json").read_text())
    assert any(
        binding["agentId"] == "dfcx-agent-001"
        and binding["sourceTag"] == "DIRECT_RESOURCE_BINDING"
        and binding["iamMember"] == "user:alice@example.com"
        and binding["scope"] == "resource"
        and binding["confidence"] == "HIGH"
        and binding["kind"] == "USER"
        for binding in identity_bindings
    )
    assert not any(
        binding["agentId"] == "re-001"
        and binding["iamMember"] == "serviceAccount:re-001@demo-proj.iam.gserviceaccount.com"
        for binding in identity_bindings
    )
    assert any(
        binding["agentId"] == "re-001"
        and binding["iamMember"] == "group:analysts@example.com"
        and binding["confidence"] == "MEDIUM"
        and binding["expanded"] is False
        and binding["kind"] == "GROUP"
        for binding in identity_bindings
    )
    assert json.loads((output_dir / "agents.json").read_text()) == [
        {
            "id": "dfcx-agent-001",
            "platform": "GOOGLE_VERTEX_AI",
            "flavor": "dialogflowcx",
            "projectId": "demo-proj",
            "location": "us-central1",
            "displayName": "Support Agent",
            "resourceName": "projects/demo-proj/locations/us-central1/agents/dfcx-agent-001",
            "sourceType": "dialogflowcx_agent",
            "runtimeIdentity": None,
            "toolIds": [],
            "knowledgeBaseIds": [],
            "guardrailId": None,
        },
        {
            "id": "re-001",
            "platform": "GOOGLE_VERTEX_AI",
            "flavor": "vertexai",
            "projectId": "demo-proj",
            "location": "us-central1",
            "displayName": "Planner Engine",
            "resourceName": "projects/demo-proj/locations/us-central1/reasoningEngines/re-001",
            "sourceType": "vertex_reasoning_engine",
            "runtimeIdentity": "serviceAccount:re-001@demo-proj.iam.gserviceaccount.com",
            "toolIds": [],
            "knowledgeBaseIds": [],
            "guardrailId": None,
        },
    ]
    assert json.loads((output_dir / "service-accounts.json").read_text()) == [
        {
            "id": "projects/demo-proj/serviceAccounts/re-001@demo-proj.iam.gserviceaccount.com",
            "platform": "GOOGLE_VERTEX_AI",
            "email": "re-001@demo-proj.iam.gserviceaccount.com",
            "projectId": "demo-proj",
            "linkedAgentIds": ["re-001"],
        }
    ]
    manifest = json.loads((output_dir / "manifest.json").read_text())
    assert manifest["schemaVersion"] == "1.0"
    assert manifest["platform"] == "GOOGLE_VERTEX_AI"
    assert manifest["collectionMode"] == "fixtures"
    assert manifest["flavorsIncluded"] == ["dialogflowcx", "vertexai"]
    assert manifest["projectIdsScanned"] == ["demo-proj"]
    assert manifest["locationsScanned"] == ["us-central1"]
    assert manifest["agentCount"] == 2
    assert manifest["identityBindingCount"] == len(identity_bindings)
    assert manifest["serviceAccountCount"] == 1
    assert manifest["artifacts"] == {
        "agents": {"file": "agents.json", "count": 2},
        "identityBindings": {
            "file": "identity-bindings.json",
            "count": len(identity_bindings),
        },
        "serviceAccounts": {"file": "service-accounts.json", "count": 1},
    }
    assert manifest["warnings"] == [
        "Project-level IAM fallback was used for one or more agents.",
        "Group expansion is not performed in v1.",
    ]
    assert isinstance(manifest["generatedAt"], str)
    assert manifest["generatedAt"].endswith("Z")


def test_fixture_mode_requires_iam_fixture_path(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    config_path.write_text(
        (
            '{"flavor":"dialogflowcx",'
            '"dialogflow_fixture_path":"tests/fixtures/dialogflow_agent.json",'
            '"output_dir":"build/artifacts",'
            '"fixtures":true}'
        )
    )

    args = parse_args(["--config", str(config_path)])
    with pytest.raises(ValueError, match="iam_fixture_path is required"):
        load_config(args)


def test_fixture_mode_iam_fixture_path_must_exist(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    config_path.write_text(
        (
            '{"flavor":"dialogflowcx",'
            '"dialogflow_fixture_path":"tests/fixtures/dialogflow_agent.json",'
            '"iam_fixture_path":"tests/fixtures/missing_iam.json",'
            '"output_dir":"build/artifacts",'
            '"fixtures":true}'
        )
    )

    args = parse_args(["--config", str(config_path)])
    with pytest.raises(ValueError, match="iam_fixture_path does not exist"):
        load_config(args)


def test_fixture_mode_iam_fixture_path_must_be_file(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    config_path.write_text(
        (
            '{"flavor":"dialogflowcx",'
            '"dialogflow_fixture_path":"tests/fixtures/dialogflow_agent.json",'
            '"iam_fixture_path":"tests/fixtures",'
            '"output_dir":"build/artifacts",'
            '"fixtures":true}'
        )
    )

    args = parse_args(["--config", str(config_path)])
    with pytest.raises(ValueError, match="iam_fixture_path must be a file"):
        load_config(args)
