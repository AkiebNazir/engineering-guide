"""
08 — Config Loader — Reference Solution
==========================================

See `08_config_loader_explanation.py` for the full spec and rationale.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any

import tomllib

DEFAULTS: dict[str, Any] = {
    "host": "0.0.0.0",
    "port": 8080,
    "timeout_seconds": 30.0,
    "log_level": "INFO",
    "debug": False,
}

_VALID_LOG_LEVELS = frozenset({"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"})

_TRUE_STRINGS = frozenset({"1", "true", "yes", "on"})
_FALSE_STRINGS = frozenset({"0", "false", "no", "off"})


class ConfigError(Exception):
    """Raised for any config loading, coercion, or validation failure."""


@dataclass(frozen=True)
class AppConfig:
    host: str = "0.0.0.0"
    port: int = 8080
    timeout_seconds: float = 30.0
    log_level: str = "INFO"
    debug: bool = False

    def __post_init__(self) -> None:
        # Validation runs once, after all three layers are already merged
        # into concrete typed values — it only ever needs to check ranges
        # and membership, never re-parse strings.
        if not (1 <= self.port <= 65535):
            raise ConfigError(f"port out of range 1-65535: {self.port!r}")
        if self.timeout_seconds <= 0:
            raise ConfigError(f"timeout_seconds must be > 0: {self.timeout_seconds!r}")
        if self.log_level not in _VALID_LOG_LEVELS:
            raise ConfigError(
                f"log_level must be one of {sorted(_VALID_LOG_LEVELS)}: "
                f"{self.log_level!r}"
            )


def _load_toml_layer(toml_path: Path | None) -> dict[str, Any]:
    """A missing file is not an error (config files are often optional);
    a malformed one raises loudly rather than silently falling back to
    defaults, which would hide a real deploy mistake."""
    if toml_path is None or not toml_path.exists():
        return {}
    try:
        with toml_path.open("rb") as f:
            return tomllib.load(f)
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"invalid TOML in {toml_path}: {exc}") from exc


def _coerce_env_value(field_name: str, raw: str, target_type: type) -> Any:
    if target_type is bool:
        # bool("false") is True in Python -- the classic env-var bug this
        # dedicated branch exists to avoid. Match a small known vocabulary
        # instead of relying on Python's truthiness of non-empty strings.
        lowered = raw.strip().lower()
        if lowered in _TRUE_STRINGS:
            return True
        if lowered in _FALSE_STRINGS:
            return False
        raise ConfigError(f"env var for {field_name!r} is not a valid bool: {raw!r}")
    if target_type in (int, float):
        try:
            return target_type(raw)
        except ValueError as exc:
            raise ConfigError(
                f"env var for {field_name!r} is not a valid "
                f"{target_type.__name__}: {raw!r}"
            ) from exc
    # str (or anything else): pass through unchanged.
    return raw


def _load_env_layer(env: Mapping[str, str]) -> dict[str, Any]:
    overrides: dict[str, Any] = {}
    for f in fields(AppConfig):
        env_name = f"APP_{f.name.upper()}"
        if env_name in env:
            # DEFAULTS' value types drive coercion rather than f.type,
            # since `from __future__ import annotations` makes f.type a
            # string ("bool", "int", ...) rather than the live type object.
            target_type = type(DEFAULTS[f.name])
            overrides[f.name] = _coerce_env_value(f.name, env[env_name], target_type)
    return overrides


def load_config(
    toml_path: Path | None = None,
    *,
    env: Mapping[str, str] | None = None,
) -> AppConfig:
    """Merge DEFAULTS -> TOML file -> environment variables, then construct
    and validate an AppConfig. Each layer's dict.update() shallow-overrides
    the previous one, which is sufficient for this flat config shape."""
    if env is None:
        env = os.environ

    merged: dict[str, Any] = dict(DEFAULTS)
    merged.update(_load_toml_layer(toml_path))
    merged.update(_load_env_layer(env))

    return AppConfig(**merged)


# ---------------------------------------------------------------------------
# Best practices
# ---------------------------------------------------------------------------
# - Validate once, after merging every layer — never mid-layer, so a value
#   invalid in an earlier layer but fixed by a later one never raises.
# - Inject the environment mapping (`env: Mapping[str, str] | None`) instead
#   of reading `os.environ` directly inside the merge logic — tests pass a
#   plain dict and never risk polluting the real process environment or
#   fighting over global state under parallel test execution.
# - A dedicated `ConfigError` hierarchy means callers can catch exactly
#   "config is bad" without also catching unrelated `ValueError`s from
#   elsewhere in the app.
# - `frozen=True` turns "don't mutate config after startup" from a
#   convention into an enforced invariant.
#
# Alternative approaches
# -----------------------
# - `pydantic-settings` gives you this whole pattern (layered sources +
#   coercion + validation) out of the box, at the cost of the dependency
#   this curriculum's problem 08 explicitly avoids to keep the mechanism
#   visible.
# - `argparse` can serve as a fourth layer (CLI flags) with the same
#   left-to-right override philosophy — CLI flags typically outrank env
#   vars, which outrank file config, which outranks code defaults.
# - For nested config, a small recursive-merge helper (`deep_merge(a, b)`)
#   replaces the flat `dict.update` calls, and `AppConfig` would need
#   nested dataclasses with their own `__post_init__` validation.
