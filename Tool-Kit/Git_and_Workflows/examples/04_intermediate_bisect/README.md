# Intermediate: Git Bisect
**Goal:** Use binary search with `git bisect` to efficiently find the exact commit that introduced a bug.
**Key Concepts:** [Git Bisect (The Bug Hunter)](../../Git_and_Workflows.md#3-git-bisect-the-bug-hunter)
**Prerequisites:** Git installed, Bash shell
**Step-by-Step Execution:**
1. Run `./setup_bisect.sh`
   - *Expected output:* A new directory `bisect-repo` is created with 10 commits. A bug was introduced in the middle.
2. `cd bisect-repo`
3. Start the bisect process: `git bisect start`
4. Mark the current commit as bad: `git bisect bad`
5. Mark an older commit as good: `git bisect good HEAD~9`
**Try it yourself:** Inspect `math.js`. If it uses `+`, run `git bisect good`. If it uses `-`, run `git bisect bad`. Repeat until Git identifies the offending commit!
**Teardown:** Run `cd .. && rm -rf bisect-repo`
