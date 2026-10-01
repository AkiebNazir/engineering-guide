"""
LEVEL 10 (capstone) - A small file organizer, exercising levels 1-9 together
================================================================================
You will learn (by combining almost everything from levels 1-9)
  * .rglob("*") to find every file in a tree, regardless of nesting depth
  * .suffix/.stem to classify files and build collision-safe alternate names
  * .mkdir(parents=True, exist_ok=True) to create destination buckets lazily
  * .replace() to move each file atomically into its bucket, with .stat()
    used afterwards to prove no bytes were lost in the process

Run: python level_10_file_organizer_capstone.py
"""
import shutil
import tempfile
from pathlib import Path


def organize_by_extension(source: Path, dest: Path) -> dict[str, int]:
    """Move every file under source into dest/<extension>/, resolving
    filename collisions with a numeric suffix. Returns a per-bucket count."""
    counts: dict[str, int] = {}
    for path in sorted(source.rglob("*")):
        if not path.is_file():
            continue

        bucket = path.suffix.lstrip(".") or "noext"
        bucket_dir = dest / bucket
        bucket_dir.mkdir(parents=True, exist_ok=True)

        target = bucket_dir / path.name
        n = 1
        while target.exists():                       # resolve a name collision
            target = bucket_dir / f"{path.stem}_{n}{path.suffix}"
            n += 1

        path.replace(target)                          # atomic move into place
        counts[bucket] = counts.get(bucket, 0) + 1
    return counts


if __name__ == "__main__":
    workspace = Path(tempfile.mkdtemp(prefix="pystdlib_pathlib_lvl10_"))
    source = workspace / "messy"
    dest = workspace / "organized"

    try:
        (source / "photos").mkdir(parents=True)
        (source / "docs" / "nested").mkdir(parents=True)

        (source / "photos" / "vacation.jpg").write_bytes(b"\xff\xd8jpeg-bytes")
        (source / "docs" / "report.txt").write_text("quarterly report")
        (source / "docs" / "nested" / "report.txt").write_text("a DIFFERENT report, same name")
        (source / "docs" / "readme").write_text("no extension at all")

        original_sizes = {p: p.stat().st_size for p in source.rglob("*") if p.is_file()}

        counts = organize_by_extension(source, dest)

        assert counts == {"jpg": 1, "txt": 2, "noext": 1}
        assert dest.resolve().is_dir()

        # the extension buckets exist and hold what we expect
        jpg_files = sorted(dest.glob("jpg/*"))
        txt_files = sorted(dest.glob("txt/*"))
        noext_files = sorted(dest.glob("noext/*"))
        assert [p.name for p in jpg_files] == ["vacation.jpg"]
        assert [p.name for p in noext_files] == ["readme"]

        # the two same-named report.txt files collided and were resolved --
        # one keeps its name, the other got a numeric suffix, both survived
        txt_names = sorted(p.name for p in txt_files)
        assert txt_names == ["report.txt", "report_1.txt"]
        contents = {p.read_text() for p in txt_files}
        assert contents == {"quarterly report", "a DIFFERENT report, same name"}

        # every byte made it across intact -- total size before == total after
        assert sum(original_sizes.values()) == sum(p.stat().st_size for p in dest.rglob("*") if p.is_file())

        # the source tree is now empty of files (everything was moved, not copied)
        assert not any(p.is_file() for p in source.rglob("*"))

        print(f"organized {sum(counts.values())} files into {len(counts)} buckets: {counts}")
        print("OK")
    finally:
        shutil.rmtree(workspace, ignore_errors=True)
