"""Table-driven tests for the filesystem walker against the reference solution."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_SOLUTION_PATH = Path(__file__).parent / "07_filesystem_walker_solution.py"
_spec = importlib.util.spec_from_file_location(
    "filesystem_walker_solution", _SOLUTION_PATH
)
assert _spec is not None and _spec.loader is not None
_solution = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _solution
_spec.loader.exec_module(_solution)

walk_files = _solution.walk_files
total_size = _solution.total_size
find_duplicates = _solution.find_duplicates


def _make_tree(root: Path) -> None:
    (root / "a.py").write_text("print('a')")
    (root / "b.txt").write_text("hello")
    sub = root / "sub"
    sub.mkdir()
    (sub / "c.py").write_text("print('c')")
    excluded = root / ".git"
    excluded.mkdir()
    (excluded / "should_not_be_seen.py").write_text("x" * 1000)


def test_walk_files_lists_everything(tmp_path: Path) -> None:
    _make_tree(tmp_path)
    found = {p.relative_to(tmp_path) for p in walk_files(tmp_path)}
    assert found == {
        Path("a.py"),
        Path("b.txt"),
        Path("sub/c.py"),
        Path(".git/should_not_be_seen.py"),
    }


def test_walk_files_prunes_excluded_dirs(tmp_path: Path) -> None:
    _make_tree(tmp_path)
    found = {
        p.relative_to(tmp_path)
        for p in walk_files(tmp_path, exclude_dirs=frozenset({".git"}))
    }
    assert found == {Path("a.py"), Path("b.txt"), Path("sub/c.py")}


def test_walk_files_prune_avoids_stat_inside_excluded_dir(tmp_path: Path) -> None:
    _make_tree(tmp_path)
    # A directory that would raise on stat/listdir if ever descended into.
    forbidden = tmp_path / "node_modules"
    forbidden.mkdir()
    (forbidden / "x.py").write_text("should never be touched")

    found = list(walk_files(tmp_path, exclude_dirs=frozenset({"node_modules"})))
    assert all("node_modules" not in p.parts for p in found)


def test_walk_files_pattern_filters_by_filename(tmp_path: Path) -> None:
    _make_tree(tmp_path)
    found = {p.relative_to(tmp_path) for p in walk_files(tmp_path, pattern="*.py")}
    assert found == {Path("a.py"), Path("sub/c.py"), Path(".git/should_not_be_seen.py")}


def test_total_size_empty_dir_is_zero(tmp_path: Path) -> None:
    assert total_size(tmp_path) == 0


def test_total_size_matches_manual_sum(tmp_path: Path) -> None:
    _make_tree(tmp_path)
    expected = sum(p.stat().st_size for p in tmp_path.rglob("*") if p.is_file())
    assert total_size(tmp_path) == expected


def test_total_size_respects_pattern(tmp_path: Path) -> None:
    _make_tree(tmp_path)
    expected = (tmp_path / "a.py").stat().st_size + (
        tmp_path / "sub" / "c.py"
    ).stat().st_size
    expected += (tmp_path / ".git" / "should_not_be_seen.py").stat().st_size
    assert total_size(tmp_path, pattern="*.py") == expected


def test_find_duplicates_identifies_identical_content_regardless_of_name(
    tmp_path: Path,
) -> None:
    (tmp_path / "one.txt").write_text("same content")
    (tmp_path / "two.txt").write_text("same content")
    (tmp_path / "unique.txt").write_text("different content")

    dups = find_duplicates(tmp_path)
    assert len(dups) == 1
    (group,) = dups.values()
    assert {p.name for p in group} == {"one.txt", "two.txt"}


def test_find_duplicates_no_false_positives_for_unique_files(tmp_path: Path) -> None:
    (tmp_path / "one.txt").write_text("aaa")
    (tmp_path / "two.txt").write_text("bbb")
    assert find_duplicates(tmp_path) == {}


def test_find_duplicates_empty_dir(tmp_path: Path) -> None:
    assert find_duplicates(tmp_path) == {}
