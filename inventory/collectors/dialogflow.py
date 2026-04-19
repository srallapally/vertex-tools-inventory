# inventory/collectors/dialogflow.py
from __future__ import annotations

import json
import urllib.parse
import urllib.request
from pathlib import Path

import google.auth
import google.auth.transport.requests

from inventory.config import InventoryConfig
from inventory.models import NormalizedAgent
from inventory.normalize.agents import normalize_dialogflow_agent

_SCOPES = ["https://www.googleapis.com/auth/cloud-platform"]
def _base_url(location: str) -> str:
    return f"https://{location}-dialogflow.googleapis.com/v3"


def collect_dialogflow_agents_from_fixture(fixture_path: Path) -> list[NormalizedAgent]:
    payload = json.loads(fixture_path.read_text())
    agents = payload.get("agents", [])
    return [normalize_dialogflow_agent(agent) for agent in agents]


def collect_dialogflow_agents_live(config: InventoryConfig) -> list[NormalizedAgent]:
    credentials, _ = google.auth.default(scopes=_SCOPES)
    auth_request = google.auth.transport.requests.Request()

    agents: list[NormalizedAgent] = []
    for project_id in config.project_ids:
        for location in config.locations:
            agents.extend(_list_agents(project_id, location, credentials, auth_request))
    return agents


def _list_agents(
    project_id: str,
    location: str,
    credentials: google.auth.credentials.Credentials,
    auth_request: google.auth.transport.requests.Request,
) -> list[NormalizedAgent]:
    agents: list[NormalizedAgent] = []
    page_token: str | None = None

    while True:
        if not credentials.valid:
            credentials.refresh(auth_request)

        params: dict[str, str] = {}
        if page_token:
            params["pageToken"] = page_token
        base_url = _base_url(location)
        url = f"{base_url}/projects/{project_id}/locations/{location}/agents"
        if params:
            url = f"{url}?{urllib.parse.urlencode(params)}"

        request = urllib.request.Request(
            url,
            headers={"Authorization": f"Bearer {credentials.token}"},
        )
        with urllib.request.urlopen(request) as response:
            body = json.loads(response.read().decode("utf-8"))

        for agent in body.get("agents", []):
            resource_name = agent.get("name")
            if not resource_name:
                continue
            agents.append(
                normalize_dialogflow_agent(
                    {
                        "agent_id": resource_name.rsplit("/", 1)[-1],
                        "project_id": project_id,
                        "location": location,
                        "display_name": agent.get("displayName", ""),
                        "resource_name": resource_name,
                        "runtime_identity": None,
                    }
                )
            )

        page_token = body.get("nextPageToken")
        if not page_token:
            break

    return agents