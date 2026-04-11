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

    assert len(bindings) == 1
    assert bindings[0].iamMember == "user:bob@example.com"
    assert bindings[0].sourceTag == "INHERITED_PROJECT_BINDING"
    assert bindings[0].scope == "project"
    assert bindings[0].permissions == ["read"]


def test_unexpanded_group_binding() -> None:
    agent = _agent()
    bindings = normalize_identity_bindings(
        agents=[agent],
        resource_policies={
            agent.resourceName: {
                "bindings": [
                    {
                        "role": "roles/viewer",
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


def test_empty_iam_response_returns_no_bindings() -> None:
    agent = _agent()
    bindings = normalize_identity_bindings(
        agents=[agent],
        resource_policies={agent.resourceName: {"bindings": []}},
        project_policies={agent.projectId: {"bindings": []}},
    )

    assert bindings == []
