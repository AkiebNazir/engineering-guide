"""
LEVEL 03 (core) - a realistic idiom: human-facing vs machine-facing JSON
==========================================================================
You will learn
  * writing one config file for humans (indent=2, sort_keys=True) to read/diff
  * writing the same data compact, for sending over a wire, in the same program
  * merging a loaded config with defaults -- a very common real pattern

Run: python level_03_config_file_idiom.py
"""
import json
import os
import shutil
import tempfile

DEFAULTS = {"host": "0.0.0.0", "port": 8080, "debug": False, "retries": 3}


def load_config_with_defaults(path: str) -> dict:
    """Load user overrides from disk and layer them on top of DEFAULTS."""
    try:
        with open(path, encoding="utf-8") as f:
            overrides = json.load(f)
    except FileNotFoundError:
        overrides = {}
    merged = dict(DEFAULTS)
    merged.update(overrides)
    return merged


def save_human_readable(path: str, config: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, sort_keys=True)
        f.write("\n")


def to_wire_format(config: dict) -> str:
    """Compact form for sending over a network -- no wasted whitespace."""
    return json.dumps(config, sort_keys=True, separators=(",", ":"))


def main() -> None:
    tmpdir = tempfile.mkdtemp()
    path = os.path.join(tmpdir, "app.json")
    try:
        # No file yet -- pure defaults.
        cfg = load_config_with_defaults(path)
        assert cfg == DEFAULTS

        # A user writes a partial override file by hand.
        with open(path, "w", encoding="utf-8") as f:
            f.write('{"port": 9090, "debug": true}\n')

        cfg = load_config_with_defaults(path)
        assert cfg == {"host": "0.0.0.0", "port": 9090, "debug": True, "retries": 3}

        save_human_readable(path, cfg)
        with open(path, encoding="utf-8") as f:
            pretty = f.read()
        assert pretty.startswith("{\n")
        assert '"debug": true' in pretty

        wire = to_wire_format(cfg)
        assert " " not in wire            # separators=(",", ":") strips all extra whitespace
        assert json.loads(wire) == cfg
    finally:
        shutil.rmtree(tmpdir)

    print("OK")


if __name__ == "__main__":
    main()
