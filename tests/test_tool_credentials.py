# tests/test_tool_credentials.py
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from inventory.models import NormalizedToolCredential
from inventory.normalize.tool_credentials import (
    derive_webhook_auth,
    make_tool_key,
    normalize_tool_credentials,
)
from inventory.collectors.webhooks import collect_webhooks_from_fixture
from inventory.writers.json_writer import write_tool_credentials_json


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_AGENT = "projects/demo-proj/locations/us-central1/agents/dfcx-agent-001"
_WEBHOOK_BASE = f"{_AGENT}/webhooks"
FIXTURE_PATH = Path("tests/fixtures/tool_credentials_fixture.json")


def _webhook(name: str, **kwargs) -> dict:
    return {"name": f"{_WEBHOOK_BASE}/{name}", **kwargs}


def _expected_id(tool_id: str) -> str:
    digest = hashlib.sha1(tool_id.encode("utf-8")).hexdigest()
    return f"tc-{digest[:16]}"


# ---------------------------------------------------------------------------
# derive_webhook_auth
# ---------------------------------------------------------------------------

def test_service_account_via_generic_web_service() -> None:
    webhook = _webhook(
        "w1",
        genericWebService={"uri": "https://example.com", "serviceAccount": "sa@proj.iam.gserviceaccount.com"},
    )
    auth_type, credential_ref = derive_webhook_auth(webhook)
    assert auth_type == "SERVICE_ACCOUNT"
    assert credential_ref == "sa@proj.iam.gserviceaccount.com"


def test_oauth_via_oauth_config() -> None:
    webhook = _webhook("w2", genericWebService={"uri": "https://example.com", "oauthConfig": {"clientId": "x"}})
    auth_type, credential_ref = derive_webhook_auth(webhook)
    assert auth_type == "OAUTH"
    assert credential_ref == "oauth"


def test_api_key_via_request_headers() -> None:
    webhook = _webhook("w3", genericWebService={"uri": "https://example.com", "requestHeaders": {"X-Api-Key": "secret"}})
    auth_type, credential_ref = derive_webhook_auth(webhook)
    assert auth_type == "API_KEY"
    assert credential_ref == "api-key"


def test_service_account_via_service_directory() -> None:
    webhook = _webhook(
        "w4",
        serviceDirectory={"service": "projects/p/locations/l/namespaces/n/services/svc"},
    )
    auth_type, credential_ref = derive_webhook_auth(webhook)
    assert auth_type == "SERVICE_ACCOUNT"
    assert credential_ref == "projects/p/locations/l/namespaces/n/services/svc"


def test_none_when_no_auth_config() -> None:
    webhook = _webhook("w5", genericWebService={"uri": "https://example.com"})
    auth_type, credential_ref = derive_webhook_auth(webhook)
    assert auth_type == "NONE"
    assert credential_ref == ""


def test_service_account_takes_precedence_over_oauth() -> None:
    webhook = _webhook(
        "w6",
        genericWebService={
            "uri": "https://example.com",
            "serviceAccount": "sa@proj.iam.gserviceaccount.com",
            "oauthConfig": {"clientId": "x"},
        },
    )
    auth_type, _ = derive_webhook_auth(webhook)
    assert auth_type == "SERVICE_ACCOUNT"


# ---------------------------------------------------------------------------
# make_tool_key
# ---------------------------------------------------------------------------

def test_make_tool_key_replaces_slashes() -> None:
    tool_id = "projects/p/locations/l/agents/a/webhooks/w"
    assert make_tool_key(tool_id) == "projects_p_locations_l_agents_a_webhooks_w"


def test_make_tool_key_no_slashes_unchanged() -> None:
    assert make_tool_key("no-slashes-here") == "no-slashes-here"


# ---------------------------------------------------------------------------
# normalize_tool_credentials
# ---------------------------------------------------------------------------

def test_none_auth_entries_excluded() -> None:
    webhooks = [
        _webhook("sa-hook", genericWebService={"uri": "https://x.com", "serviceAccount": "sa@p.iam.gserviceaccount.com"}),
        _webhook("no-auth", genericWebService={"uri": "https://x.com"}),
    ]
    results = normalize_tool_credentials(webhooks)
    assert len(results) == 1
    assert results[0].authType == "SERVICE_ACCOUNT"


def test_all_three_auth_types_normalized() -> None:
    webhooks = [
        _webhook("sa-hook", genericWebService={"serviceAccount": "sa@p.iam.gserviceaccount.com"}),
        _webhook("oauth-hook", genericWebService={"oauthConfig": {"clientId": "x"}}),
        _webhook("key-hook", genericWebService={"requestHeaders": {"X-Key": "v"}}),
    ]
    results = normalize_tool_credentials(webhooks)
    assert len(results) == 3
    auth_types = {r.authType for r in results}
    assert auth_types == {"SERVICE_ACCOUNT", "OAUTH", "API_KEY"}


def test_credential_ref_never_contains_secret_value() -> None:
    webhooks = [
        _webhook("key-hook", genericWebService={"requestHeaders": {"X-Api-Key": "my-secret-key-value"}}),
    ]
    results = normalize_tool_credentials(webhooks)
    assert results[0].credentialRef == "api-key"
    assert "my-secret-key-value" not in results[0].credentialRef


def test_tool_id_is_full_resource_name() -> None:
    tool_id = f"{_WEBHOOK_BASE}/payment-gateway"
    webhooks = [_webhook("payment-gateway", genericWebService={"serviceAccount": "sa@p.iam.gserviceaccount.com"})]
    results = normalize_tool_credentials(webhooks)
    assert results[0].toolId == tool_id


def test_tool_key_derived_from_tool_id() -> None:
    webhooks = [_webhook("payment-gateway", genericWebService={"serviceAccount": "sa@p.iam.gserviceaccount.com"})]
    results = normalize_tool_credentials(webhooks)
    assert results[0].toolKey == results[0].toolId.replace("/", "_")


def test_id_is_deterministic_hash_of_tool_id() -> None:
    tool_id = f"{_WEBHOOK_BASE}/payment-gateway"
    webhooks = [_webhook("payment-gateway", genericWebService={"serviceAccount": "sa@p.iam.gserviceaccount.com"})]
    results = normalize_tool_credentials(webhooks)
    assert results[0].id == _expected_id(tool_id)


def test_agent_id_extracted_from_webhook_name() -> None:
    webhooks = [_webhook("payment-gateway", genericWebService={"serviceAccount": "sa@p.iam.gserviceaccount.com"})]
    results = normalize_tool_credentials(webhooks)
    assert results[0].agentId == _AGENT


def test_project_id_and_location_extracted_from_webhook_name() -> None:
    webhooks = [_webhook("payment-gateway", genericWebService={"serviceAccount": "sa@p.iam.gserviceaccount.com"})]
    results = normalize_tool_credentials(webhooks)
    assert results[0].projectId == "demo-proj"
    assert results[0].location == "us-central1"


def test_webhook_with_missing_name_skipped() -> None:
    webhooks = [{"genericWebService": {"serviceAccount": "sa@p.iam.gserviceaccount.com"}}]
    results = normalize_tool_credentials(webhooks)
    assert results == []


def test_empty_webhook_list_returns_empty() -> None:
    assert normalize_tool_credentials([]) == []


# ---------------------------------------------------------------------------
# collect_webhooks_from_fixture
# ---------------------------------------------------------------------------

def test_fixture_loads_all_four_webhooks() -> None:
    webhooks = collect_webhooks_from_fixture(FIXTURE_PATH)
    assert len(webhooks) == 4


def test_fixture_webhook_names_are_full_resource_names() -> None:
    webhooks = collect_webhooks_from_fixture(FIXTURE_PATH)
    for webhook in webhooks:
        assert webhook["name"].startswith("projects/")
        assert "/webhooks/" in webhook["name"]


def test_fixture_produces_three_credentials_after_normalization() -> None:
    webhooks = collect_webhooks_from_fixture(FIXTURE_PATH)
    results = normalize_tool_credentials(webhooks)
    assert len(results) == 3
    auth_types = {r.authType for r in results}
    assert auth_types == {"SERVICE_ACCOUNT", "OAUTH", "API_KEY"}


# ---------------------------------------------------------------------------
# write_tool_credentials_json
# ---------------------------------------------------------------------------

def test_writer_produces_correct_json(tmp_path: Path) -> None:
    tool_id = f"{_WEBHOOK_BASE}/payment-gateway"
    credentials = [
        NormalizedToolCredential(
            id=_expected_id(tool_id),
            toolId=tool_id,
            toolKey=make_tool_key(tool_id),
            toolType="WEBHOOK",
            agentId=_AGENT,
            authType="SERVICE_ACCOUNT",
            credentialRef="sa@demo-proj.iam.gserviceaccount.com",
            projectId="demo-proj",
            location="us-central1",
        )
    ]
    path = write_tool_credentials_json(tmp_path, credentials)
    assert path.name == "tool-credentials.json"
    payload = json.loads(path.read_text())
    assert len(payload) == 1
    assert payload[0]["toolId"] == tool_id
    assert payload[0]["toolKey"] == make_tool_key(tool_id)
    assert payload[0]["authType"] == "SERVICE_ACCOUNT"
    assert payload[0]["credentialRef"] == "sa@demo-proj.iam.gserviceaccount.com"
    assert payload[0]["toolType"] == "WEBHOOK"
    assert payload[0]["agentId"] == _AGENT
    assert payload[0]["projectId"] == "demo-proj"
    assert payload[0]["location"] == "us-central1"


def test_writer_empty_list_produces_empty_array(tmp_path: Path) -> None:
    path = write_tool_credentials_json(tmp_path, [])
    payload = json.loads(path.read_text())
    assert payload == []