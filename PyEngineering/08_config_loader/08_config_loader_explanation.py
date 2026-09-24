"""
08 — Config Loader
====================

WHAT
----
Build a layered configuration loader for a small service:

    defaults (in code)  →  TOML file (optional)  →  environment variables

Each layer overrides the one before it. The result is validated into a
frozen `AppConfig` dataclass with type coercion and range/format checks, so
the rest of the codebase gets a fully-typed, already-validated config object
instead of passing raw dicts around.

WHY THIS MATTERS
----------------
Real services need config from multiple sources: a checked-in default, an
environment-specific file (dev/staging/prod), and per-deploy environment
variable overrides (the twelve-factor-app pattern — secrets and per-instance
values come from env vars, not files, so they never land in source control
or a shared config file). Getting the *layering order* and *validation
timing* right matters: validation must happen once, after all layers are
merged, so a bad override anywhere fails loudly at startup — not deep inside
request handling three hours later.

This module intentionally uses **only** `tomllib` (stdlib, read-only, 3.11+)
and `dataclasses` — no `pydantic` — per this curriculum's fixed toolchain
choice for problem 08: dataclasses + `__post_init__` cover real-world
validation needs without a dependency, and force you to understand what a
validation library does for you under the hood.

LAYERING SPEC
-------------
1. **Defaults** — hardcoded literal values in `DEFAULTS: dict[str, Any]`
   below (host, port, timeout, log level, feature flags).
2. **TOML file** — if a path is given and exists, `tomllib.load()` it and
   shallow-merge its top-level keys over the defaults. A missing file is not
   an error (config files are often optional/environment-specific); a
   malformed one (`tomllib.TOMLDecodeError`) must raise immediately.
3. **Environment variables** — for each config field, an env var named
   `APP_<FIELD_NAME_UPPER>` (e.g. `APP_PORT`, `APP_LOG_LEVEL`) overrides
   whatever the previous layers produced. Env vars are always strings, so
   this layer must coerce them to the field's target type (`int`, `bool`,
   etc.) — a bad coercion (e.g. `APP_PORT=not-a-number`) must raise a clear
   `ConfigError`, not an opaque `ValueError` from deep inside `int()`.
4. **Validation** — construct `AppConfig(**merged)`; `__post_init__` checks
   ranges/formats (port in 1-65535, log level in a known set, timeout > 0)
   and raises `ConfigError` with a message naming the offending field.

SPEC
----
    class ConfigError(Exception): ...

    @dataclass(frozen=True)
    class AppConfig:
        host: str = "0.0.0.0"
        port: int = 8080
        timeout_seconds: float = 30.0
        log_level: str = "INFO"
        debug: bool = False

        def __post_init__(self) -> None: ...  # validation

    DEFAULTS: dict[str, Any]  # matches AppConfig field defaults

    def load_config(
        toml_path: Path | None = None,
        *,
        env: Mapping[str, str] | None = None,   # defaults to os.environ
    ) -> AppConfig:
        "Merge DEFAULTS -> toml_path (if present) -> env vars, then
        construct/validate an AppConfig."

ACCEPTANCE CRITERIA
--------------------
- Calling `load_config()` with no arguments and no relevant env vars set
  returns an `AppConfig` equal to one built from `DEFAULTS` alone.
- A TOML file overriding a subset of keys leaves the rest at defaults.
- An env var overrides both the default AND a TOML-file value for the same
  key (env wins — it's the last layer).
- `APP_PORT="abc"` raises `ConfigError` (not a raw `ValueError`/`TypeError`).
- `port=70000` (out of range, however it got there — file or env) raises
  `ConfigError` from `__post_init__`.
- `log_level="TRACE"` (not in the allowed set) raises `ConfigError`.
- A missing TOML path is silently ignored (defaults/env still apply); a
  TOML file with invalid syntax raises (does not silently fall back).
- `AppConfig` is frozen/immutable (accidental mutation after startup is a
  bug class this should make impossible) — attempting to set an attribute
  after construction raises `dataclasses.FrozenInstanceError`.
- The `env` parameter (injectable mapping) means tests never need to
  actually mutate `os.environ` — this is the config-loader analogue of
  problem 07's "always take root as a parameter" testability lesson.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULTS: dict[str, Any] = {
    "host": "0.0.0.0",
    "port": 8080,
    "timeout_seconds": 30.0,
    "log_level": "INFO",
    "debug": False,
}

_VALID_LOG_LEVELS = frozenset({"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"})


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
        """TODO: validate port range, timeout > 0, log_level membership.

        Raise ConfigError (not assert / bare ValueError) naming the field
        and the bad value.
        """
        raise NotImplementedError


def _load_toml_layer(toml_path: Path | None) -> dict[str, Any]:
    """TODO: return {} if toml_path is None or doesn't exist. Otherwise
    tomllib.load() it (binary mode!) and return its top-level dict. Let
    tomllib.TOMLDecodeError propagate (or wrap in ConfigError — pick one and
    be consistent)."""
    raise NotImplementedError


def _coerce_env_value(field_name: str, raw: str, target_type: type) -> Any:
    """TODO: coerce the string env var to target_type.

    - bool: accept a small known set of truthy/falsy strings case-
      insensitively (e.g. "true"/"false", "1"/"0") — do NOT use `bool(raw)`,
      which is True for any non-empty string including "false"!
    - int/float: wrap the conversion, raise ConfigError with field name on
      failure instead of letting ValueError leak out raw.
    - str: pass through unchanged.
    """
    raise NotImplementedError


def _load_env_layer(env: Mapping[str, str]) -> dict[str, Any]:
    """TODO: for each field in AppConfig's dataclass fields, look up
    APP_<FIELD_UPPER> in env; if present, coerce via _coerce_env_value using
    the field's declared type and add to the returned overrides dict.
    """
    raise NotImplementedError


def load_config(
    toml_path: Path | None = None,
    *,
    env: Mapping[str, str] | None = None,
) -> AppConfig:
    """TODO: merge DEFAULTS -> toml layer -> env layer (env parameter
    defaults to os.environ when None), then construct AppConfig(**merged).
    Let AppConfig.__post_init__'s ConfigError propagate.
    """
    raise NotImplementedError


# ---------------------------------------------------------------------------
# Hints
# ---------------------------------------------------------------------------
# - `tomllib.load(f)` requires `f` opened in binary mode ("rb") — it raises
#   TypeError on a text-mode file, unlike `json.load`.
# - `dataclasses.fields(AppConfig)` gives you (name, type) pairs to drive
#   the env-var layer generically instead of hand-writing one branch per
#   field.
# - `field.type` on a dataclass field can be a string (from `from __future__
#   import annotations`) rather than the real type object — if you hit this,
#   either drive coercion off `DEFAULTS`'s value types with `type(default)`,
#   or use `typing.get_type_hints(AppConfig)` to resolve string annotations.
# - Keep `_coerce_env_value` and `__post_init__` doing different jobs:
#   coercion turns strings into the right Python type; validation checks
#   that the (already-typed) value is in range/allowed.
#
# Pitfalls
# --------
# - `bool("false")` is `True` — a classic env-var config bug. Never use the
#   `bool` constructor directly on a raw env string.
# - Deep-merging when you meant shallow-merging (or vice versa) — this spec
#   is intentionally shallow (flat config), so `dict.update` semantics are
#   sufficient; note in your solution why a nested config would need real
#   recursive merging.
# - Validating *before* all layers are merged — a value that's invalid at
#   the defaults layer but corrected by an env var should not raise.
# - Swallowing `tomllib.TOMLDecodeError` silently — a malformed file should
#   be loud, not treated the same as a missing one.
#
# Stretch goals
# -------------
# - Support nested TOML tables mapped to nested dataclasses.
# - Add a `--dump-effective-config` style `to_dict()` / logging helper that
#   redacts fields named like secrets before printing (real services must
#   never log raw secrets on startup).
# - Add a `source: dict[str, str]` companion result recording which layer
#   won for each field (defaults/file/env) — invaluable for debugging "why
#   is prod using the wrong port" incidents.
