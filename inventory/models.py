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
