from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path


def build_gcs_object_paths(
    output_dir: Path,
    bucket_prefix: str,
    timestamp: str,
    write_latest: bool,
) -> dict[Path, list[str]]:
    files = sorted(path for path in output_dir.iterdir() if path.is_file())
    normalized_prefix = bucket_prefix.strip("/")
    runs_prefix = _join_path(normalized_prefix, "runs", timestamp)
    latest_prefix = _join_path(normalized_prefix, "latest")

    destinations: dict[Path, list[str]] = {}
    for file_path in files:
        object_paths = [_join_path(runs_prefix, file_path.name)]
        if write_latest:
            object_paths.append(_join_path(latest_prefix, file_path.name))
        destinations[file_path] = object_paths

    return destinations


def upload_directory_to_gcs(
    output_dir: Path,
    bucket_name: str,
    bucket_prefix: str,
    write_latest: bool,
    timestamp: str | None = None,
    client=None,
) -> dict[str, str | list[str] | None]:
    if timestamp is None:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    destinations = build_gcs_object_paths(
        output_dir=output_dir,
        bucket_prefix=bucket_prefix,
        timestamp=timestamp,
        write_latest=write_latest,
    )

    if client is None:
        try:
            from google.cloud import storage
        except ImportError as exc:
            raise RuntimeError(
                "google-cloud-storage is required for GCS uploads. "
                "Install it to enable batch uploads."
            ) from exc
        client = storage.Client()
    bucket = client.bucket(bucket_name)
    uploaded_uris: list[str] = []

    for file_path, object_paths in destinations.items():
        for object_path in object_paths:
            bucket.blob(object_path).upload_from_filename(str(file_path))
            uploaded_uris.append(f"gs://{bucket_name}/{object_path}")

    normalized_prefix = bucket_prefix.strip("/")
    run_prefix = _join_path(normalized_prefix, "runs", timestamp)
    latest_prefix = _join_path(normalized_prefix, "latest") if write_latest else None

    return {
        "uploaded_uris": uploaded_uris,
        "run_prefix": run_prefix,
        "latest_prefix": latest_prefix,
    }


def _join_path(*parts: str) -> str:
    return "/".join(part.strip("/") for part in parts if part and part.strip("/"))
