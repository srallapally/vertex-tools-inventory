from __future__ import annotations

ROLE_PERMISSION_MAP: dict[str, list[str]] = {
    "roles/dialogflow.client": ["invoke"],
    "roles/aiplatform.user": ["invoke"],
    "roles/viewer": ["read"],
    "roles/dialogflow.viewer": ["read"],
    "roles/aiplatform.viewer": ["read"],
    "roles/owner": ["manage"],
    "roles/editor": ["manage"],
    "roles/dialogflow.admin": ["manage"],
    "roles/aiplatform.admin": ["manage"],
}


def normalize_permissions_for_role(iam_role: str) -> list[str]:
    return ROLE_PERMISSION_MAP.get(iam_role, [])
