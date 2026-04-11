from inventory.models import NormalizedAgent
from inventory.normalize.service_accounts import normalize_service_accounts


def _agent(
    *,
    agent_id: str,
    runtime_identity: str | None,
    flavor: str = "vertexai",
) -> NormalizedAgent:
    return NormalizedAgent(
        id=agent_id,
        platform="GOOGLE_VERTEX_AI",
        flavor=flavor,
        projectId="demo-proj",
        location="us-central1",
        displayName=f"Agent {agent_id}",
        resourceName=f"projects/demo-proj/locations/us-central1/reasoningEngines/{agent_id}",
        sourceType="vertex_reasoning_engine",
        runtimeIdentity=runtime_identity,
        toolIds=[],
        knowledgeBaseIds=[],
        guardrailId=None,
    )


def test_one_reasoning_engine_with_runtime_service_account() -> None:
    service_accounts = normalize_service_accounts(
        [
            _agent(
                agent_id="re-001",
                runtime_identity="serviceAccount:re-001@demo-proj.iam.gserviceaccount.com",
            )
        ]
    )

    assert [service_account.to_dict() for service_account in service_accounts] == [
        {
            "id": "projects/demo-proj/serviceAccounts/re-001@demo-proj.iam.gserviceaccount.com",
            "platform": "GOOGLE_VERTEX_AI",
            "email": "re-001@demo-proj.iam.gserviceaccount.com",
            "projectId": "demo-proj",
            "linkedAgentIds": ["re-001"],
        }
    ]


def test_two_agents_sharing_runtime_service_account_are_deduplicated() -> None:
    service_accounts = normalize_service_accounts(
        [
            _agent(agent_id="re-001", runtime_identity="shared@demo-proj.iam.gserviceaccount.com"),
            _agent(
                agent_id="re-002",
                runtime_identity="serviceAccount:shared@demo-proj.iam.gserviceaccount.com",
            ),
        ]
    )

    assert len(service_accounts) == 1
    assert service_accounts[0].to_dict() == {
        "id": "projects/demo-proj/serviceAccounts/shared@demo-proj.iam.gserviceaccount.com",
        "platform": "GOOGLE_VERTEX_AI",
        "email": "shared@demo-proj.iam.gserviceaccount.com",
        "projectId": "demo-proj",
        "linkedAgentIds": ["re-001", "re-002"],
    }


def test_dialogflow_agent_without_runtime_identity_does_not_emit_service_account() -> None:
    service_accounts = normalize_service_accounts(
        [_agent(agent_id="dfcx-agent-001", runtime_identity=None, flavor="dialogflowcx")]
    )

    assert service_accounts == []
