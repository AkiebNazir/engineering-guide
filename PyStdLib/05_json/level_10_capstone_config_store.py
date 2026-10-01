"""
LEVEL 10 (capstone) - a small, crash-safe JSON config store, levels 1-9 together
==================================================================================
You will learn
  * combining atomic writes, custom datetime encode/decode, strict decoding,
    and duplicate-key detection into one small realistic store
  * a ConfigStore class: load (tolerant of a missing file, strict about
    malformed JSON), save (atomically, human-readable), and a change log
    kept as JSON Lines in an in-memory buffer for the demo

Run: python level_10_capstone_config_store.py
"""
import io
import json
import os
import shutil
import tempfile
from datetime import datetime, timezone


def _encode(obj):
    if isinstance(obj, datetime):
        return {"__datetime__": obj.isoformat()}
    raise TypeError(f"cannot serialize {type(obj)!r}")


def _decode_pairs(pairs):
    """One combined object_pairs_hook: reject duplicate keys AND restore datetimes.

    object_pairs_hook and object_hook can't both run on the same object (per the
    json docs, object_pairs_hook takes priority when both are passed) -- so
    duplicate detection and custom decoding are merged into a single hook here.
    """
    seen = {}
    for key, value in pairs:
        if key in seen:
            raise ValueError(f"duplicate key in config: {key!r}")
        seen[key] = value
    if "__datetime__" in seen:
        return datetime.fromisoformat(seen["__datetime__"])
    return seen


class ConfigStore:
    """A tiny crash-safe, strictly-decoded JSON config store."""

    def __init__(self, path: str):
        self.path = path
        self.change_log = io.StringIO()   # JSON Lines audit trail, in memory

    def load(self) -> dict:
        try:
            with open(self.path, encoding="utf-8") as f:
                return json.load(f, object_pairs_hook=_decode_pairs)
        except FileNotFoundError:
            return {}

    def save(self, config: dict) -> None:
        directory = os.path.dirname(self.path) or "."
        fd, tmp_path = tempfile.mkstemp(dir=directory, prefix=".tmp-", suffix=".json")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, sort_keys=True, default=_encode, allow_nan=False)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, self.path)
        except BaseException:
            os.remove(tmp_path)
            raise
        json.dump({"saved_at": datetime.now(timezone.utc).isoformat(), "keys": sorted(config)},
                  self.change_log)
        self.change_log.write("\n")


def main() -> None:
    tmpdir = tempfile.mkdtemp()
    path = os.path.join(tmpdir, "config.json")
    try:
        store = ConfigStore(path)
        assert store.load() == {}   # no file yet -- tolerant default

        deployed_at = datetime(2026, 3, 1, 9, 0, tzinfo=timezone.utc)
        store.save({"replicas": 3, "deployed_at": deployed_at})
        store.save({"replicas": 5, "deployed_at": deployed_at})

        loaded = store.load()
        assert loaded["replicas"] == 5
        assert loaded["deployed_at"] == deployed_at   # datetime round-tripped, not a dict

        # malformed/duplicate-key files are rejected loudly, not silently accepted
        with open(path, "w", encoding="utf-8") as f:
            f.write('{"replicas": 1, "replicas": 2}')
        try:
            store.load()
            raise AssertionError("expected ValueError for duplicate key")
        except ValueError:
            pass

        # the in-memory change log recorded both successful saves as JSON Lines
        store.change_log.seek(0)
        log_lines = [json.loads(line) for line in store.change_log if line.strip()]
        assert len(log_lines) == 2
        assert all(entry["keys"] == ["deployed_at", "replicas"] for entry in log_lines)
    finally:
        shutil.rmtree(tmpdir)

    print("OK")


if __name__ == "__main__":
    main()
