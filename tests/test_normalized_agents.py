from pathlib import Path
import json

from inventory.collectors.dialogflow import collect_dialogflow_agents_from_fixture
from inventory.collectors.reasoning_engines import collect_reasoning_engines_from_fixture
from inventory.writers.json_writer import (
    write_agents_json,
    write_identity_bindings_json,
    write_manifest_json,
    write_service_accounts_json,
)


def test_dialogflow_fixture_normalizes_agent() -> None:
    fixture = Path("tests/fixtures/dialogflow_agent.json")
    agents = collect_dialogflow_agents_from_fixture(fixture)

    assert len(agents) == 1
    assert agents[0].flavor == "dialogflowcx"
    assert agents[0].sourceType == "dialogflowcx_agent"
    assert agents[0].id == "dfcx-agent-001"
    assert agents[0].runtimeIdentity is None


def test_reasoning_engine_fixture_normalizes_agent() -> None:
    fixture = Path("tests/fixtures/reasoning_engine.json")
    agents = collect_reasoning_engines_from_fixture(fixture)

    assert len(agents) == 1
    assert agents[0].flavor == "vertexai"
    assert agents[0].sourceType == "vertex_reasoning_engine"
    assert agents[0].id == "re-001"
    assert agents[0].runtimeIdentity == "serviceAccount:re-001@demo-proj.iam.gserviceaccount.com"


def test_writer_outputs_agents_identity_bindings_and_manifest(tmp_path: Path) -> None:
    fixture = Path("tests/fixtures/dialogflow_agent.json")
    agents = collect_dialogflow_agents_from_fixture(fixture)

    agents_path = write_agents_json(tmp_path, agents)
    identity_path = write_identity_bindings_json(tmp_path, [])
    service_accounts_path = write_service_accounts_json(tmp_path, [])
    manifest_path = write_manifest_json(
        tmp_path,
        "fixtures",
        ["dialogflowcx"],
        ["demo-proj"],
        ["us-central1"],
        len(agents),
        0,
        0,
        ["No identity bindings were generated."],
    )

    assert agents_path.name == "agents.json"
    assert identity_path.name == "identity-bindings.json"
    assert manifest_path.name == "manifest.json"
    assert service_accounts_path.name == "service-accounts.json"
    assert agents_path.exists()
    assert identity_path.exists()
    assert manifest_path.exists()
    assert service_accounts_path.exists()
    assert json.loads(agents_path.read_text()) == [
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
        }
    ]
    manifest_payload = json.loads(manifest_path.read_text())
    assert manifest_payload["schemaVersion"] == "1.0"
    assert manifest_payload["platform"] == "GOOGLE_VERTEX_AI"
    assert manifest_payload["collectionMode"] == "fixtures"
    assert manifest_payload["flavorsIncluded"] == ["dialogflowcx"]
    assert manifest_payload["projectIdsScanned"] == ["demo-proj"]
    assert manifest_payload["locationsScanned"] == ["us-central1"]
    assert manifest_payload["agentCount"] == 1
    assert manifest_payload["identityBindingCount"] == 0
    assert manifest_payload["serviceAccountCount"] == 0
    assert manifest_payload["artifacts"] == {
        "agents": {"file": "agents.json", "count": 1},
        "identityBindings": {"file": "identity-bindings.json", "count": 0},
        "serviceAccounts": {"file": "service-accounts.json", "count": 0},
    }
    assert manifest_payload["warnings"] == ["No identity bindings were generated."]
    assert isinstance(manifest_payload["generatedAt"], str)
    assert manifest_payload["generatedAt"].endswith("Z")


def test_writer_manifest_supports_live_collection_mode(tmp_path: Path) -> None:
    manifest_path = write_manifest_json(
        tmp_path,
        "live",
        ["vertexai"],
        ["demo-proj"],
        ["us-central1"],
        0,
        0,
        0,
        [],
    )

    manifest_payload = json.loads(manifest_path.read_text())
    assert manifest_payload["collectionMode"] == "live"
