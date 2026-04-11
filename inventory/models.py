from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal

Flavor = Literal["dialogflowcx", "vertexai"]


@dataclass(frozen=True)
class NormalizedAgent:
    id: str
    flavor: Flavor
    project_id: str
    location: str
    display_name: str
    resource_name: str
    source_type: str

    def to_dict(self) -> dict:
        return asdict(self)
