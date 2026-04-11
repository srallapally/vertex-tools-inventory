from pathlib import Path

from inventory.writers.gcs_writer import build_gcs_object_paths


def test_build_gcs_object_paths_generates_run_paths(tmp_path: Path) -> None:
    (tmp_path / "agents.json").write_text("[]\n")
    (tmp_path / "manifest.json").write_text("{}\n")

    destinations = build_gcs_object_paths(
        output_dir=tmp_path,
        bucket_prefix="inventory/prod",
        timestamp="20260411T120000Z",
        write_latest=False,
    )

    assert destinations[tmp_path / "agents.json"] == [
        "inventory/prod/runs/20260411T120000Z/agents.json"
    ]
    assert destinations[tmp_path / "manifest.json"] == [
        "inventory/prod/runs/20260411T120000Z/manifest.json"
    ]


def test_build_gcs_object_paths_generates_run_and_latest_paths(tmp_path: Path) -> None:
    (tmp_path / "service-accounts.json").write_text("[]\n")

    destinations = build_gcs_object_paths(
        output_dir=tmp_path,
        bucket_prefix="/inventory/prod/",
        timestamp="20260411T120000Z",
        write_latest=True,
    )

    assert destinations[tmp_path / "service-accounts.json"] == [
        "inventory/prod/runs/20260411T120000Z/service-accounts.json",
        "inventory/prod/latest/service-accounts.json",
    ]
