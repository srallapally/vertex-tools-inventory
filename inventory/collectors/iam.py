# inventory/collectors/iam.py
from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from pathlib import Path

import google.auth
import google.auth.transport.requests

from inventory.models import NormalizedAgent

_SCOPES = ["https://www.googleapis.com/auth/cloud-platform"]
_DIALOGFLOW_BASE = "https://dialogflow.googleapis.com/v3"
_CRM_BASE = "https://cloudresourcemanager.googleapis.com/v1"

LOGGER = logging.getLogger(__name__)

PolicyMap = dict[str, dict]


def collect_iam_policies_from_fixture(fixture_path: Path) -> tuple[PolicyMap, PolicyMap]:
    payload = json.loads(fixture_path.read_text())
    resource_policies = payload.get("resource_iam_policies", {})
    project_policies = payload.get("project_iam_policies", {})
    return resource_policies, project_policies


def collect_iam_policies_live(agents: list[NormalizedAgent]) -> tuple[PolicyMap, PolicyMap]:
    credentials, _ = google.auth.default(scopes=_SCOPES)
    auth_request = google.auth.transport.requests.Request()

    resource_policies: PolicyMap = {}
    project_policies: PolicyMap = {}

    for agent in agents:
        resource_policy = _get_resource_policy(agent, credentials, auth_request)

        if resource_policy is not None:
            if resource_policy.get("bindings"):
                resource_policies[agent.resourceName] = resource_policy
            else:
                LOGGER.warning(
                    "Resource-level IAM policy is empty for %s — falling back to project policy",
                    agent.resourceName,
                )
                _collect_project_policy(agent.projectId, credentials, auth_request, project_policies)
            continue

        # resource-level call failed (non-2xx or 404) — already logged; no fallback
        # (option b: permission misconfiguration should not be masked)

    return resource_policies, project_policies


def _get_resource_policy(
    agent: NormalizedAgent,
    credentials: google.auth.credentials.Credentials,
    auth_request: google.auth.transport.requests.Request,
) -> dict | None:
    """
    Returns the IAM policy dict on success (may have empty bindings),
    or None if the HTTP call failed (non-2xx). Logs a WARNING on failure.
    """
    if agent.flavor == "dialogflowcx":
        location = agent.location or "us-central1"
        url = f"https://{location}-dialogflow.googleapis.com/v3/{agent.resourceName}:getIamPolicy"
    else:
        url = f"https://{agent.location}-aiplatform.googleapis.com/v1/{agent.resourceName}:getIamPolicy"

    return _post_get_iam_policy(url, label=agent.resourceName, credentials=credentials, auth_request=auth_request)


def _collect_project_policy(
    project_id: str,
    credentials: google.auth.credentials.Credentials,
    auth_request: google.auth.transport.requests.Request,
    project_policies: PolicyMap,
) -> None:
    project_key = f"projects/{project_id}"
    if project_key in project_policies:
        return

    url = f"{_CRM_BASE}/projects/{project_id}:getIamPolicy"
    LOGGER.info("Fetching project-level IAM fallback for %s", project_id)
    policy = _post_get_iam_policy(url, label=project_key, credentials=credentials, auth_request=auth_request)
    if policy is not None:
        project_policies[project_key] = policy


def _post_get_iam_policy(
    url: str,
    label: str,
    credentials: google.auth.credentials.Credentials,
    auth_request: google.auth.transport.requests.Request,
) -> dict | None:
    """
    POST to a getIamPolicy endpoint. Returns parsed response dict on 2xx,
    None on any HTTP error. Logs WARNING on failure.
    """
    if not credentials.valid:
        credentials.refresh(auth_request)

    request = urllib.request.Request(
        url,
        data=b"{}",
        headers={
            "Authorization": f"Bearer {credentials.token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = ""
        try:
            body = exc.read().decode("utf-8")[:500]
        except Exception:
            pass
        LOGGER.warning(
            "getIamPolicy failed for %s — HTTP %s: %s",
            label,
            exc.code,
            body,
        )
        return None
    except urllib.error.URLError as exc:
        LOGGER.warning("getIamPolicy failed for %s — %s", label, exc.reason)
        return None