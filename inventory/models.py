from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal

Flavor = Literal["dialogflowcx", "vertexai"]


@dataclass(frozen=True)
class NormalizedAgent:
    id: str
    platform: str
    flavor: Flavor
    projectId: str
    location: str
    displayName: str
    resourceName: str
    sourceType: str
    runtimeIdentity: str | None
    toolIds: list[str]
    knowledgeBaseIds: list[str]
    guardrailId: str | None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class NormalizedIdentityBinding:
    id: str
    agentId: str
    agentVersion: str
    principal: str
    principalType: str
    iamMember: str
    iamRole: str
    permissions: list[str]
    scope: str
    scopeType: str
    scopeResourceName: str
    sourceTag: str
    confidence: str
    kind: str
    flavor: Flavor
    expanded: bool

    def to_dict(self) -> dict:
        return asdict(self)
