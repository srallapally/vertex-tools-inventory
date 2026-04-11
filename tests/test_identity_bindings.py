from inventory.models import NormalizedAgent
from inventory.normalize.bindings import normalize_identity_bindings


def _agent() -> NormalizedAgent:
    return NormalizedAgent(
        id="agent-1",
        platform="GOOGLE_VERTEX_AI",
        flavor="dialogflowcx",
        projectId="demo-proj",
        location="us-central1",
        displayName="Support Agent",
        resourceName="projects/demo-proj/locations/us-central1/agents/agent-1",
        sourceType="dialogflowcx_agent",
        runtimeIdentity=None,
        toolIds=[],
        knowledgeBaseIds=[],
        guardrailId=None,
    )


def test_direct_resource_binding_takes_precedence() -> None:
    agent = _agent()
    bindings = normalize_identity_bindings(
        agents=[agent],
        resource_policies={
            agent.resourceName: {
                "bindings": [
                    {
                        "role": "roles/dialogflow.client",
                        "members": ["user:alice@example.com"],
                    }
                ]
            }
        },
        project_policies={
            agent.projectId: {
                "bindings": [
                    {"role": "roles/viewer", "members": ["user:bob@example.com"]}
                ]
            }
        },
    )

    assert len(bindings) == 1
    assert bindings[0].iamMember == "user:alice@example.com"
    assert bindings[0].sourceTag == "DIRECT_RESOURCE_BINDING"
    assert bindings[0].scope == "resource"
    assert bindings[0].permissions == ["invoke"]
    assert bindings[0].kind == "USER"
    assert bindings[0].confidence == "HIGH"


def test_project_fallback_binding_when_resource_missing() -> None:
    agent = _agent()
    bindings = normalize_identity_bindings(
        agents=[agent],
        resource_policies={},
        project_policies={
            f"projects/{agent.projectId}": {
                "bindings": [
                    {"role": "roles/viewer", "members": ["user:bob@example.com"]}
                ]
            }
        },
    )

    assert bindings == []


def test_unexpanded_group_binding() -> None:
    agent = _agent()
    bindings = normalize_identity_bindings(
        agents=[agent],
        resource_policies={
            agent.resourceName: {
                "bindings": [
                    {
                        "role": "roles/dialogflow.client",
                        "members": ["group:analysts@example.com"],
                    }
                ]
            }
        },
        project_policies={},
    )

    assert len(bindings) == 1
    assert bindings[0].principalType == "GROUP"
    assert bindings[0].expanded is False
    assert bindings[0].sourceTag == "UNEXPANDED_GROUP"
    assert bindings[0].permissions == ["invoke"]
    assert bindings[0].kind == "GROUP"


def test_runtime_identity_self_binding_not_emitted() -> None:
    agent = NormalizedAgent(
        **{
            **_agent().to_dict(),
            "runtimeIdentity": "serviceAccount:re-001@demo-proj.iam.gserviceaccount.com",
        }
    )
    bindings = normalize_identity_bindings(
        agents=[agent],
        resource_policies={},
        project_policies={
            f"projects/{agent.projectId}": {
                "bindings": [
                    {
                        "role": "roles/aiplatform.user",
                        "members": [
                            "serviceAccount:re-001@demo-proj.iam.gserviceaccount.com"
                        ],
                    }
                ]
            }
        },
    )

    assert bindings == []


def test_vertex_inherited_project_binding_uses_medium_confidence() -> None:
    agent = NormalizedAgent(
        **{
            **_agent().to_dict(),
            "flavor": "vertexai",
            "sourceType": "vertex_reasoning_engine",
        }
    )
    bindings = normalize_identity_bindings(
        agents=[agent],
        resource_policies={},
        project_policies={
            f"projects/{agent.projectId}": {
                "bindings": [
                    {
                        "role": "roles/aiplatform.user",
                        "members": ["user:bob@example.com"],
                    }
                ]
            }
        },
    )

    assert len(bindings) == 1
    assert bindings[0].scope == "project"
    assert bindings[0].sourceTag == "INHERITED_PROJECT_BINDING"
    assert bindings[0].confidence == "MEDIUM"


def test_empty_iam_response_returns_no_bindings() -> None:
    agent = _agent()
    bindings = normalize_identity_bindings(
        agents=[agent],
        resource_policies={agent.resourceName: {"bindings": []}},
        project_policies={agent.projectId: {"bindings": []}},
    )

    assert bindings == []
