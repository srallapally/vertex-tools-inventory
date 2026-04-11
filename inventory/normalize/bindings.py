from __future__ import annotations

import hashlib

from inventory.models import NormalizedAgent, NormalizedIdentityBinding
from inventory.normalize.roles import normalize_permissions_for_role


def normalize_identity_bindings(
    agents: list[NormalizedAgent],
    resource_policies: dict[str, dict],
    project_policies: dict[str, dict],
) -> list[NormalizedIdentityBinding]:
    bindings: list[NormalizedIdentityBinding] = []

    for agent in agents:
        resource_policy = resource_policies.get(agent.resourceName)
        resource_bindings = _policy_bindings(resource_policy)

        if resource_bindings:
            bindings.extend(
                _normalize_policy_bindings(
                    agent=agent,
                    iam_bindings=resource_bindings,
                    scope="resource",
                    scope_type="AGENT_RESOURCE",
                    scope_resource_name=agent.resourceName,
                    source_tag="DIRECT_RESOURCE_BINDING",
                    confidence="HIGH",
                )
            )
            continue

        project_policy = project_policies.get(agent.projectId) or project_policies.get(
            f"projects/{agent.projectId}"
        )
        project_bindings = _policy_bindings(project_policy)
        if not project_bindings:
            continue

        bindings.extend(
            _normalize_policy_bindings(
                agent=agent,
                iam_bindings=project_bindings,
                scope="project",
                scope_type="PROJECT",
                scope_resource_name=f"projects/{agent.projectId}",
                source_tag="INHERITED_PROJECT_BINDING",
                confidence="MEDIUM",
            )
        )

    return bindings


def _policy_bindings(policy: dict | None) -> list[dict]:
    if not policy:
        return []
    bindings = policy.get("bindings", [])
    if not isinstance(bindings, list):
        return []
    return bindings


def _normalize_policy_bindings(
    *,
    agent: NormalizedAgent,
    iam_bindings: list[dict],
    scope: str,
    scope_type: str,
    scope_resource_name: str,
    source_tag: str,
    confidence: str,
) -> list[NormalizedIdentityBinding]:
    normalized_bindings: list[NormalizedIdentityBinding] = []

    for iam_binding in iam_bindings:
        role = iam_binding.get("role")
        if not role:
            continue

        permissions = normalize_permissions_for_role(role)
        if not _is_caller_access_binding(permissions):
            continue

        for member in iam_binding.get("members", []):
            principal, principal_type = _parse_member(member)
            if _is_runtime_identity_member(
                member=member,
                principal=principal,
                runtime_identity=agent.runtimeIdentity,
            ):
                continue
            group_member = principal_type == "GROUP"
            binding_source_tag = "UNEXPANDED_GROUP" if group_member else source_tag
            binding = NormalizedIdentityBinding(
                id=_make_binding_id(agent.id, member, role, scope_resource_name),
                agentId=agent.id,
                agentVersion="latest",
                principal=principal,
                principalType=principal_type,
                iamMember=member,
                iamRole=role,
                permissions=permissions,
                scope=scope,
                scopeType=scope_type,
                scopeResourceName=scope_resource_name,
                sourceTag=binding_source_tag,
                confidence=confidence,
                kind=principal_type,
                flavor=agent.flavor,
                expanded=not group_member,
            )
            normalized_bindings.append(binding)

    return normalized_bindings


def _is_caller_access_binding(permissions: list[str]) -> bool:
    return "invoke" in permissions or "manage" in permissions


def _is_runtime_identity_member(
    *,
    member: str,
    principal: str,
    runtime_identity: str | None,
) -> bool:
    if not runtime_identity:
        return False
    return principal == runtime_identity or member == runtime_identity


def _parse_member(member: str) -> tuple[str, str]:
    if ":" not in member:
        if member == "allUsers":
            return member, "PUBLIC"
        if member == "allAuthenticatedUsers":
            return member, "AUTHENTICATED_PUBLIC"
        return member, "UNKNOWN"

    member_type, principal = member.split(":", 1)
    principal_type = {
        "user": "USER",
        "group": "GROUP",
        "serviceAccount": "SERVICE_ACCOUNT",
        "domain": "DOMAIN",
    }.get(member_type, "UNKNOWN")
    return principal, principal_type


def _make_binding_id(agent_id: str, member: str, role: str, scope_resource_name: str) -> str:
    digest = hashlib.sha1(
        f"{agent_id}|{member}|{role}|{scope_resource_name}".encode("utf-8")
    ).hexdigest()
    return f"ib-{digest[:16]}"
