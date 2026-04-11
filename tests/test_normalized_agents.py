from pathlib import Path

from inventory.collectors.dialogflow import collect_dialogflow_agents_from_fixture
from inventory.collectors.reasoning_engines import collect_reasoning_engines_from_fixture
from inventory.writers.json_writer import write_agents_json, write_manifest_json


def test_dialogflow_fixture_normalizes_agent() -> None:
    fixture = Path("tests/fixtures/dialogflow_agent.json")
    agents = collect_dialogflow_agents_from_fixture(fixture)

    assert len(agents) == 1
    assert agents[0].flavor == "dialogflowcx"
    assert agents[0].source_type == "dialogflowcx_agent"
    assert agents[0].id == "dfcx-agent-001"


def test_reasoning_engine_fixture_normalizes_agent() -> None:
    fixture = Path("tests/fixtures/reasoning_engine.json")
    agents = collect_reasoning_engines_from_fixture(fixture)

    assert len(agents) == 1
    assert agents[0].flavor == "vertexai"
    assert agents[0].source_type == "vertex_reasoning_engine"
    assert agents[0].id == "re-001"


def test_writer_outputs_agents_and_manifest(tmp_path: Path) -> None:
    fixture = Path("tests/fixtures/dialogflow_agent.json")
    agents = collect_dialogflow_agents_from_fixture(fixture)

    agents_path = write_agents_json(tmp_path, agents)
    manifest_path = write_manifest_json(tmp_path, "dialogflowcx", len(agents))

    assert agents_path.name == "agents.json"
    assert manifest_path.name == "manifest.json"
    assert agents_path.exists()
    assert manifest_path.exists()
