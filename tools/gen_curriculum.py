#!/usr/bin/env python3
"""Generate CURRICULUM.md from tools/problems.tsv (single source of truth)."""
import csv, pathlib, collections

ROOT = pathlib.Path(__file__).resolve().parent.parent
TSV = ROOT / "tools" / "problems.tsv"
OUT = ROOT / "CURRICULUM.md"

TOPIC_TITLES = {
    "01_arrays_hashing": "Arrays & Hashing",
    "02_two_pointers": "Two Pointers",
    "03_sliding_window": "Sliding Window",
    "04_prefix_sum": "Prefix Sum",
    "05_binary_search": "Binary Search",
    "06_stack": "Stack & Monotonic Stack",
    "07_queue_deque": "Queue & Deque",
    "08_linked_list": "Linked List",
    "09_recursion_backtracking": "Recursion & Backtracking",
    "10_trees": "Binary Trees",
    "11_binary_search_tree": "Binary Search Tree",
    "12_heap_priority_queue": "Heap / Priority Queue",
    "13_trie": "Trie (Prefix Tree)",
    "14_graphs": "Graphs",
    "15_advanced_graphs": "Advanced Graphs",
    "16_dp_1d": "Dynamic Programming (1D)",
    "17_dp_2d": "Dynamic Programming (2D)",
    "18_greedy": "Greedy",
    "19_intervals": "Intervals",
    "20_bit_manipulation": "Bit Manipulation",
    "21_math_geometry": "Math & Geometry",
    "22_sorting_algorithms": "Sorting Algorithms",
    "23_string_algorithms": "String Algorithms",
    "24_matrix": "Matrix",
    "25_design": "Design",
    "26_segment_tree_fenwick": "Segment Tree & Fenwick Tree",
    "27_algorithms": "Classic Algorithms (Randomized, Divide & Conquer, Quickselect)",
    "28_recursion_backtracking": "Recursion Mastery (Progressive Ladder)",
}

def snake(slug):
    return slug.replace("-", "_")

def main():
    with TSV.open() as fh:
        rows = list(csv.DictReader(fh, delimiter="\t"))

    by_topic = collections.OrderedDict()
    for r in rows:
        by_topic.setdefault(r["topic"], []).append(r)

    diffs = collections.Counter(r["diff"] for r in rows)
    L = []
    A = L.append

    A("# Curriculum Index\n")
    A(f"**{len(rows)} LeetCode problems** across **{len(by_topic)} topics**, "
      f"in Python and Go.\n")
    A(f"Easy **{diffs['Easy']}** · Medium **{diffs['Medium']}** · Hard **{diffs['Hard']}**\n")
    A("Generated from `tools/problems.tsv` by `tools/gen_curriculum.py` — "
      "edit the TSV, not this file.\n")
    A("---\n")
    A("## Layout\n")
    A("Every topic folder opens with `_TOPIC_GUIDE.md`: what the structure is, how it works")
    A("*internally* in that language, how to build it from scratch, every algorithm that")
    A("operates on it, and when to reach for it. Then the problems.\n")
    A("```")
    A("PyDSA/01_arrays_hashing/")
    A("  _TOPIC_GUIDE.md                  <- read this first")
    A("  004_two_sum_question.py          <- problem + explanation + your stub")
    A("  004_two_sum_solution.py          <- solution + step-by-step walkthrough")
    A("")
    A("GoDSA/01_arrays_hashing/")
    A("  _TOPIC_GUIDE.md")
    A("  004_two_sum/")
    A("    question.go                    <- problem + explanation + your stub")
    A("    solution.go                    <- solution + walkthrough + main()")
    A("```\n")
    A("Run them:\n")
    A("```bash")
    A("python  PyDSA/01_arrays_hashing/004_two_sum_solution.py")
    A("cd GoDSA && go run ./01_arrays_hashing/004_two_sum")
    A("```\n")
    A("---\n")
    A("## Progress\n")
    A("| # | Topic | Problems | Guide | Written |")
    A("|:--:|---|:--:|:--:|:--:|")
    for topic, items in by_topic.items():
        n = len(items)
        guide = (ROOT / "PyDSA" / topic / "_TOPIC_GUIDE.md").exists()
        done = sum(
            1 for r in items
            if (ROOT / "PyDSA" / topic /
                f"{r['seq']}_{snake(r['slug'])}_solution.py").exists()
        )
        num = topic.split("_")[0]
        A(f"| {num} | {TOPIC_TITLES[topic]} | {n} | "
          f"{'✅' if guide else '⬜'} | {done}/{n} |")
    total_done = sum(
        1 for r in rows
        if (ROOT / "PyDSA" / r["topic"] /
            f"{r['seq']}_{snake(r['slug'])}_solution.py").exists()
    )
    A(f"| | **Total** | **{len(rows)}** | | **{total_done}/{len(rows)}** |\n")
    A("---\n")

    for topic, items in by_topic.items():
        num = topic.split("_")[0]
        A(f"## {num} · {TOPIC_TITLES[topic]}\n")
        A(f"`PyDSA/{topic}/` · `GoDSA/{topic}/`\n")
        A("| # | LC | Problem | Difficulty |")
        A("|:--:|:--:|---|:--:|")
        for r in items:
            url = f"https://leetcode.com/problems/{r['slug']}/"
            A(f"| {r['seq']} | {r['lc']} | [{r['title']}]({url}) | {r['diff']} |")
        A("")

    OUT.write_text("\n".join(L) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}: {len(rows)} problems, {len(by_topic)} topics")

if __name__ == "__main__":
    main()
