# inventory/collectors/webhooks.py
from __future__ import annotations

import json
import urllib.request
import urllib.error
from pathlib import Path

import google.auth
import google.auth.transport.requests

from inventory.models import NormalizedAgent

_SCOPES = ["https://www.googleapis.com/auth/cloud-platform"]


def collect_webhooks_from_fixture(fixture_path: Path) -> list[dict]:
    """
    Load raw webhook dicts from fixture file.
    Expected shape: {"webhooks": [<raw Dialogflow CX webhook API response>, ...]}
    """
    payload = json.loads(fixture_path.read_text())
    return payload.get("webhooks", [])


def collect_webhooks_live(agents: list[NormalizedAgent]) -> list[dict]:
    """
    Fetch raw webhook dicts for all Dialogflow CX agents via REST.
    Only agents with flavor=dialogflowcx are processed.
    Authentication uses google.auth.default() with cloud-platform scope.
    """
    credentials, _ = google.auth.default(scopes=_SCOPES)
    auth_request = google.auth.transport.requests.Request()

    webhooks: list[dict] = []
    for agent in agents:
        if agent.flavor != "dialogflowcx":
            continue
        webhooks.extend(_list_webhooks(agent.resourceName, credentials, auth_request))
    return webhooks


def _list_webhooks(
    agent_resource_name: str,
    credentials: google.auth.credentials.Credentials,
    auth_request: google.auth.transport.requests.Request,
) -> list[dict]:
    if not credentials.valid:
        credentials.refresh(auth_request)

    parts = agent_resource_name.split("/")
    location = parts[3] if len(parts) > 3 else "us-central1"
    url = f"https://{location}-dialogflow.googleapis.com/v3/{agent_resource_name}/webhooks"
    request = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {credentials.token}"},
    )
    try:
        with urllib.request.urlopen(request) as response:
            body = json.loads(response.read().decode("utf-8"))
            return body.get("webhooks", [])
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return []
        raise