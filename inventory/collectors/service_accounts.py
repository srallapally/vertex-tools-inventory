# inventory/collectors/service_accounts.py
from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request

import google.auth
import google.auth.transport.requests

from inventory.models import NormalizedServiceAccount

_SCOPES = ["https://www.googleapis.com/auth/cloud-platform"]
_IAM_BASE = "https://iam.googleapis.com/v1"

LOGGER = logging.getLogger(__name__)

# Fields to retain from each key object in the keys LIST response
_KEY_FIELDS = {"name", "keyType", "validAfterTime", "validBeforeTime", "keyAlgorithm"}


def collect_service_accounts_live(
    service_accounts: list[NormalizedServiceAccount],
) -> dict[str, dict]:
    """
    Fetches full SA metadata and key list for each NormalizedServiceAccount.
    Returns a dict keyed by SA resource name (same as NormalizedServiceAccount.id)
    mapping to the enrichment payload. Missing or failed SAs are logged and skipped.
    """
    if not service_accounts:
        return {}

    credentials, _ = google.auth.default(scopes=_SCOPES)
    auth_request = google.auth.transport.requests.Request()

    enrichment: dict[str, dict] = {}
    for sa in service_accounts:
        data = _fetch_sa_enrichment(sa, credentials, auth_request)
        if data is not None:
            enrichment[sa.id] = data

    return enrichment


def _fetch_sa_enrichment(
    sa: NormalizedServiceAccount,
    credentials: google.auth.credentials.Credentials,
    auth_request: google.auth.transport.requests.Request,
) -> dict | None:
    if not credentials.valid:
        credentials.refresh(auth_request)

    resource = f"projects/{sa.projectId}/serviceAccounts/{sa.email}"
    url = f"{_IAM_BASE}/{resource}"

    sa_data = _get_json(url, credentials)
    if sa_data is None:
        LOGGER.warning("Could not fetch SA metadata for %s — skipping enrichment", sa.email)
        return None

    keys_url = f"{url}/keys"
    keys_data = _get_json(keys_url, credentials)
    if keys_data is None:
        LOGGER.warning("Could not fetch keys for %s — continuing without key metadata", sa.email)
        keys = []
    else:
        keys = [
            {k: v for k, v in key.items() if k in _KEY_FIELDS}
            for key in keys_data.get("keys", [])
        ]

    return {
        "name": sa_data.get("name"),
        "displayName": sa_data.get("displayName"),
        "description": sa_data.get("description"),
        "uniqueId": sa_data.get("uniqueId"),
        "oauth2ClientId": sa_data.get("oauth2ClientId"),
        "disabled": sa_data.get("disabled", False),
        "createTime": sa_data.get("createTime"),
        "keysJson": json.dumps(keys),
        "keyCount": len(keys),
    }


def _get_json(
    url: str,
    credentials: google.auth.credentials.Credentials,
) -> dict | None:
    request = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {credentials.token}"},
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
        LOGGER.warning("GET %s failed — HTTP %s: %s", url, exc.code, body)
        return None
    except urllib.error.URLError as exc:
        LOGGER.warning("GET %s failed — %s", url, exc.reason)
        return None