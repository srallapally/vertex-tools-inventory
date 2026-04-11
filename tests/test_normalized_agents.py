from pathlib import Path
import json

from inventory.collectors.dialogflow import collect_dialogflow_agents_from_fixture
from inventory.collectors.reasoning_engines import collect_reasoning_engines_from_fixture
from inventory.writers.json_writer import write_agents_json, write_manifest_json


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
    assert agents[0].runtimeIdentity == "re-001@demo-proj.iam.gserviceaccount.com"


def test_writer_outputs_agents_and_manifest(tmp_path: Path) -> None:
    fixture = Path("tests/fixtures/dialogflow_agent.json")
    agents = collect_dialogflow_agents_from_fixture(fixture)

    agents_path = write_agents_json(tmp_path, agents)
    manifest_path = write_manifest_json(tmp_path, "dialogflowcx", len(agents))

    assert agents_path.name == "agents.json"
    assert manifest_path.name == "manifest.json"
    assert agents_path.exists()
    assert manifest_path.exists()
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
