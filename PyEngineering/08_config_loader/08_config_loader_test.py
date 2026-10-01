"""Table-driven tests for the layered config loader against the reference solution."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_SOLUTION_PATH = Path(__file__).parent / "08_config_loader_solution.py"
_spec = importlib.util.spec_from_file_location("config_loader_solution", _SOLUTION_PATH)
assert _spec is not None and _spec.loader is not None
_solution = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _solution
_spec.loader.exec_module(_solution)

load_config = _solution.load_config
AppConfig = _solution.AppConfig
ConfigError = _solution.ConfigError
DEFAULTS = _solution.DEFAULTS


def test_defaults_only_when_no_file_or_env() -> None:
    cfg = load_config(env={})
    assert cfg == AppConfig(**DEFAULTS)


def test_toml_file_overrides_subset_of_defaults(tmp_path: Path) -> None:
    toml_path = tmp_path / "config.toml"
    toml_path.write_text('port = 9090\nlog_level = "DEBUG"\n')

    cfg = load_config(toml_path, env={})

    assert cfg.port == 9090
    assert cfg.log_level == "DEBUG"
    # Untouched fields stay at defaults.
    assert cfg.host == DEFAULTS["host"]
    assert cfg.timeout_seconds == DEFAULTS["timeout_seconds"]


def test_env_overrides_both_default_and_file_value(tmp_path: Path) -> None:
    toml_path = tmp_path / "config.toml"
    toml_path.write_text("port = 9090\n")

    cfg = load_config(toml_path, env={"APP_PORT": "7000"})

    assert cfg.port == 7000


def test_env_bad_int_raises_config_error() -> None:
    with pytest.raises(ConfigError):
        load_config(env={"APP_PORT": "not-a-number"})


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("true", True),
        ("True", True),
        ("1", True),
        ("yes", True),
        ("on", True),
        ("false", False),
        ("False", False),
        ("0", False),
        ("no", False),
        ("off", False),
    ],
)
def test_env_bool_coercion(raw: str, expected: bool) -> None:
    cfg = load_config(env={"APP_DEBUG": raw})
    assert cfg.debug is expected


def test_env_bad_bool_raises_config_error() -> None:
    with pytest.raises(ConfigError):
        load_config(env={"APP_DEBUG": "maybe"})


def test_out_of_range_port_raises_config_error() -> None:
    with pytest.raises(ConfigError):
        load_config(env={"APP_PORT": "70000"})


def test_negative_timeout_raises_config_error() -> None:
    with pytest.raises(ConfigError):
        load_config(env={"APP_TIMEOUT_SECONDS": "-1"})


def test_invalid_log_level_raises_config_error() -> None:
    with pytest.raises(ConfigError):
        load_config(env={"APP_LOG_LEVEL": "TRACE"})


def test_missing_toml_path_is_silently_ignored(tmp_path: Path) -> None:
    missing = tmp_path / "does_not_exist.toml"
    cfg = load_config(missing, env={})
    assert cfg == AppConfig(**DEFAULTS)


def test_malformed_toml_raises_config_error(tmp_path: Path) -> None:
    bad = tmp_path / "bad.toml"
    bad.write_text("this is not [valid toml")
    with pytest.raises(ConfigError):
        load_config(bad, env={})


def test_app_config_is_frozen() -> None:
    import dataclasses

    cfg = load_config(env={})
    with pytest.raises(dataclasses.FrozenInstanceError):
        cfg.port = 1234  # type: ignore[misc]


def test_load_config_defaults_env_to_os_environ(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("APP_PORT", "6000")
    cfg = load_config()
    assert cfg.port == 6000
