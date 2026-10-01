"""Table-driven tests for AtomicFileStore against the reference solution."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

import pytest

_SOLUTION_PATH = Path(__file__).parent / "06_atomic_file_store_solution.py"
_spec = importlib.util.spec_from_file_location(
    "atomic_file_store_solution", _SOLUTION_PATH
)
assert _spec is not None and _spec.loader is not None
_solution = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _solution
_spec.loader.exec_module(_solution)

AtomicFileStore = _solution.AtomicFileStore


@pytest.fixture
def store(tmp_path: Path) -> Any:
    return AtomicFileStore(tmp_path)


def test_write_then_read_bytes_round_trips(store: Any) -> None:
    store.write_bytes("key1", b"hello world")
    assert store.read_bytes("key1") == b"hello world"


def test_write_then_read_text_round_trips(store: Any) -> None:
    store.write_text("key1", "héllo wörld")
    assert store.read_text("key1") == "héllo wörld"


def test_overwrite_replaces_content(store: Any) -> None:
    store.write_bytes("key1", b"first")
    store.write_bytes("key1", b"second, and longer than first")
    assert store.read_bytes("key1") == b"second, and longer than first"


def test_no_leftover_tmp_files_after_success(store: Any, tmp_path: Path) -> None:
    store.write_bytes("key1", b"data")
    remaining = list(tmp_path.iterdir())
    assert remaining == [tmp_path / "key1"]


def test_failed_write_preserves_original_content(
    store: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store.write_bytes("key1", b"original content")

    def boom_fsync(fd: int) -> None:
        raise OSError("simulated disk failure during fsync")

    monkeypatch.setattr(_solution.os, "fsync", boom_fsync)

    with pytest.raises(OSError):
        store.write_bytes("key1", b"this must never become visible")

    monkeypatch.undo()
    # Original content must still be intact — the failed write never
    # replaced the target file.
    assert store.read_bytes("key1") == b"original content"
    # No stray temp files left behind by the aborted write.
    leftovers = [p for p in tmp_path.iterdir() if p.name != "key1"]
    assert leftovers == []


def test_delete_removes_file(store: Any) -> None:
    store.write_bytes("key1", b"data")
    store.delete("key1")
    assert not store.exists("key1")


def test_delete_missing_key_raises_file_not_found(store: Any) -> None:
    with pytest.raises(FileNotFoundError):
        store.delete("does_not_exist")


def test_exists_true_and_false(store: Any) -> None:
    assert store.exists("key1") is False
    store.write_bytes("key1", b"data")
    assert store.exists("key1") is True


def test_read_missing_key_raises_file_not_found(store: Any) -> None:
    with pytest.raises(FileNotFoundError):
        store.read_bytes("does_not_exist")


@pytest.mark.parametrize(
    "bad_key",
    [
        "",
        "../escape",
        "/etc/passwd",
        "a/../../b",
        "../../etc/cron.d/x",
    ],
)
def test_path_traversal_keys_rejected(store: Any, bad_key: str) -> None:
    with pytest.raises(ValueError):
        store.write_bytes(bad_key, b"data")


def test_file_permissions_applied(tmp_path: Path) -> None:
    store = AtomicFileStore(tmp_path, file_mode=0o600)
    store.write_bytes("key1", b"data")
    mode = (tmp_path / "key1").stat().st_mode & 0o777
    assert mode == 0o600


def test_nested_key_creates_parent_directories(store: Any) -> None:
    store.write_bytes("sub/dir/key1", b"data")
    assert store.read_bytes("sub/dir/key1") == b"data"


def test_root_created_if_missing(tmp_path: Path) -> None:
    new_root = tmp_path / "does" / "not" / "exist"
    store = AtomicFileStore(new_root)
    assert new_root.is_dir()
    store.write_bytes("key1", b"data")
    assert store.read_bytes("key1") == b"data"
