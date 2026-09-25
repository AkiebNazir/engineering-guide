# Intermediate: Rebase Conflict
**Goal:** Practice resolving a merge conflict during a `git rebase` operation.
**Key Concepts:** [Rebase](../../Git_and_Workflows.md#2-rebase-git-rebase)
**Prerequisites:** Git installed, Bash shell
**Step-by-Step Execution:**
1. Run `./setup_rebase.sh`
   - *Expected output:* A new directory `conflict-repo` is created with a `main` branch and a `feature/update-line` branch that both modified the same line in `file.txt`.
2. `cd conflict-repo`
3. Switch to the feature branch: `git checkout feature/update-line`
4. Attempt a rebase: `git rebase main`
   - *Expected output:* Git will pause the rebase due to a conflict in `file.txt`.
**Try it yourself:** Open `file.txt`, resolve the conflict by removing the conflict markers (`<<<<<`, `=====`, `>>>>>`), run `git add file.txt`, and finally complete the rebase with `git rebase --continue`.
**Teardown:** Run `cd .. && rm -rf conflict-repo`
