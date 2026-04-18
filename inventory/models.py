# inventory/models.py
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


@dataclass(frozen=True)
class NormalizedServiceAccount:
    id: str
    platform: str
    email: str
    projectId: str
    linkedAgentIds: list[str]
    # OPENICF-4009: enriched from IAM SA GET + keys LIST
    name: str | None = None
    displayName: str | None = None
    description: str | None = None
    uniqueId: str | None = None
    oauth2ClientId: str | None = None
    disabled: bool = False
    createTime: str | None = None
    keysJson: str | None = None
    keyCount: int = 0

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class NormalizedToolCredential:
    id: str
    toolId: str
    toolKey: str
    toolType: str
    agentId: str
    authType: str
    credentialRef: str
    projectId: str
    location: str

    def to_dict(self) -> dict:
        return asdict(self)