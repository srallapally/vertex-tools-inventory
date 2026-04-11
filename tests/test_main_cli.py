from pathlib import Path

from main import load_config, parse_args


def _write_config(path: Path) -> None:
    path.write_text(
        (
            '{"flavor":"dialogflowcx",'
            '"fixture_path":"tests/fixtures/dialogflow_agent.json",'
            '"output_dir":"build/artifacts",'
            '"fixtures":false}'
        )
    )


def test_config_only_invocation_uses_file_values(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    _write_config(config_path)

    args = parse_args(["--config", str(config_path)])
    config = load_config(args)

    assert config.flavor == "dialogflowcx"
    assert config.output_dir == Path("build/artifacts")
    assert config.fixtures is False


def test_config_plus_flavor_overrides_file_value(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    _write_config(config_path)

    args = parse_args(["--config", str(config_path), "--flavor", "vertexai"])
    config = load_config(args)

    assert config.flavor == "vertexai"


def test_config_plus_output_dir_overrides_file_value(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    _write_config(config_path)

    args = parse_args(["--config", str(config_path), "--output-dir", "custom/out"])
    config = load_config(args)

    assert config.output_dir == Path("custom/out")


def test_config_plus_fixtures_overrides_file_value(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    _write_config(config_path)

    args = parse_args(["--config", str(config_path), "--fixtures"])
    config = load_config(args)

    assert config.fixtures is True
