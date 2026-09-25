# Basic Local Repo
**Goal:** Demonstrates how to initialize a Git repository, commit files, create branches, and merge changes.
**Key Concepts:** [Essential Git Commands](../../Git_and_Workflows.md#2-essential-git-commands), [Branching and Merging](../../Git_and_Workflows.md#4-branching-and-merging)
**Prerequisites:** Git installed, Bash shell
**Step-by-Step Execution:**
1. Run `./setup_scenario.sh`
   - *Expected output:* A new directory `my-project` is created with a Git repository initialized, commits made on `main` and `feature/add-styles` branches.
2. `cd my-project`
3. View the history: `git log --all --graph --oneline`
**Try it yourself:** Try running `git merge feature/add-styles` to merge the feature branch into `main`.
**Teardown:** Run `cd .. && rm -rf my-project`
