"""
LEVEL 06 (advanced) - measured: pretty-printed vs compact JSON, size and time
================================================================================
You will learn
  * indent= produces bigger output and costs more CPU time than the default
  * separators=(",", ":") produces the smallest possible output
  * measuring both honestly with time.perf_counter() rather than assuming

Run: python level_06_indent_measured.py
"""
import json
import time

RECORD_COUNT = 5_000


def build_data() -> list[dict]:
    return [
        {"id": i, "name": f"item-{i}", "active": i % 2 == 0, "tags": ["a", "b", "c"]}
        for i in range(RECORD_COUNT)
    ]


def time_dumps(data, **kwargs) -> tuple[float, int]:
    start = time.perf_counter()
    text = json.dumps(data, **kwargs)
    elapsed = time.perf_counter() - start
    return elapsed, len(text)


def main() -> None:
    data = build_data()

    default_time, default_size = time_dumps(data)
    indent_time, indent_size = time_dumps(data, indent=2)
    compact_time, compact_size = time_dumps(data, separators=(",", ":"))

    print(f"default:  {default_size:>8} bytes, {default_time:.4f}s")
    print(f"indent=2: {indent_size:>8} bytes, {indent_time:.4f}s")
    print(f"compact:  {compact_size:>8} bytes, {compact_time:.4f}s")

    # Size claims are structural, not timing-dependent -- always true.
    assert indent_size > default_size > compact_size, (
        "expected indent > default > compact in output size"
    )

    # This is the real, measured performance claim -- report it as it came out.
    assert default_time > 0 and indent_time > 0 and compact_time > 0
    print(f"indent=2 took {indent_time / default_time:.2f}x the default's time on this run")
    print(f"compact took {compact_time / default_time:.2f}x the default's time on this run")

    print("OK")


if __name__ == "__main__":
    main()
