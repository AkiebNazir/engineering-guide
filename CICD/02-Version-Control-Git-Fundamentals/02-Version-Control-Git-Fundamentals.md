# Version Control & Git Fundamentals

## 1. Overview & Purpose
**What is it?** Version control (or source control) is the practice of tracking and managing changes to software code. Git is a distributed version control system (DVCS) that allows multiple developers to work together on the same codebase simultaneously without overwriting each other's changes.
**Why does it exist?** Before version control, developers copied files manually (e.g., `code_final_v2_really_final.zip`), leading to lost work, conflicts, and inability to track who made what change.
**What problem does it solve?** It solves collaboration (multiple people editing code), history tracking (seeing past states), branching (working on features in isolation), and rollback (undoing mistakes).
**Where is it used?** Everywhere in software engineering.
**Where does it fit in backend/software engineering?** It is the foundational layer of CI/CD. No continuous integration is possible without a version control system to trigger pipelines upon code commits.

## 2. Prerequisites
- Basic understanding of files, directories, and the command line (Terminal).
- No prior knowledge of version control is assumed.

## 3. Complete Theory
- **Repository (Repo):** A directory where Git has been initialized to start version controlling files.
- **Commit:** A snapshot of your repository at a specific point in time. Contains metadata like author, timestamp, and a message.
- **Branch:** An independent line of development. The default branch is usually `main` or `master`.
- **Merge:** Integrating changes from one branch into another.
- **Clone:** Downloading a remote repository to your local machine.
- **Push / Pull:** Uploading local commits to a remote server (Push) or downloading remote commits to your local machine (Pull).
- **Working Directory / Staging Area (Index) / Local Repo:** The three states of Git files. Untracked/Modified -> Staged -> Committed.

## 4. Theory + Example
**Concept: The Staging Area**
Git separates the act of editing files from the act of committing them. You must explicitly `add` files to the staging area before committing.

```bash
# Initialize a new git repository
git init

# Create a file
echo "Hello Git" > hello.txt

# File is currently modified but not staged
git status

# Stage the file
git add hello.txt

# Commit the file
git commit -m "Initial commit"
```

## 5. Visual Explanation

```arch
node a "Working Directory" at 0,0 icon=folder color=slate
node b "Staging Area" at 1,0 icon=doc color=amber
node c "Local Repository" at 2,0 icon=db color=blue
node d "Remote Repository" at 3,0 icon=cloud color=purple
a -> b : "git add"
b -> c : "git commit"
c -> d : "git push"
d -> c : "git pull"
c -> a : "git checkout"
```
*Diagram: The Git workflow across its different states.*

## 6. How It Works Internally
Git models data as a Directed Acyclic Graph (DAG). Every commit is an object identified by a SHA-1 hash.
- **Blob:** Stores file content.
- **Tree:** Stores directory structure (file names and references to blobs).
- **Commit:** Points to a tree, a parent commit(s), and author metadata.
When you branch, Git simply creates a new pointer to a specific commit. When you merge, Git walks the DAG to find a common ancestor and creates a new merge commit.

## 7. Real-World Engineering Usage
In backend systems, Git is used in workflows like **GitFlow** or **Trunk-Based Development**.
- **Trunk-Based Development:** Developers commit frequently to `main` using feature flags. Preferred in modern CI/CD.
- **Feature Branching:** Developers create a branch `feature/auth`, work on it, and open a Pull Request (PR) to merge into `main` after code review.

## 8. Failure & Debugging
- **Merge Conflicts:** Occurs when two branches modify the same line of the same file. Git halts the merge and asks you to resolve it manually.
- **Debugging Example:** 
  ```bash
  # Git outputs: CONFLICT (content): Merge conflict in server.go
  # Open server.go, find the <<<<<<< HEAD markers, fix the code, then:
  git add server.go
  git commit -m "Resolve merge conflict"
  ```
- **Detached HEAD:** You checked out a specific commit instead of a branch. If you commit now, it won't belong to any branch. Fix: `git checkout -b new-branch`.

## 9. Production Concerns
- **Security:** Do not commit secrets (API keys, passwords). Use `.gitignore` and secret scanning tools.
- **Reliability:** Push to remote repositories (GitHub/GitLab) so local disk failure doesn't lose code.
- **Scalability:** Very large files or monorepos can slow down Git. Use Git LFS (Large File Storage) or shallow clones.

## 10. Practical Projects — Exactly 5 in Go
*(Links to directories containing full project code and instructions)*
- [Go Project 1: Basic Local Git Workflow](./go-project-1)
- [Go Project 2: Branching and Merging](./go-project-2)
- [Go Project 3: Handling Merge Conflicts](./go-project-3)
- [Go Project 4: Using Git Hooks for Pre-commit Linting](./go-project-4)
- [Go Project 5: Automated Versioning and Tagging in CI](./go-project-5)

## 11. Practical Projects — Exactly 5 in Python
*(Links to directories containing full project code and instructions)*
- [Python Project 1: Basic Local Git Workflow](./python-project-1)
- [Python Project 2: Branching and Merging](./python-project-2)
- [Python Project 3: Handling Merge Conflicts](./python-project-3)
- [Python Project 4: Using Git Hooks for Pre-commit Linting](./python-project-4)
- [Python Project 5: Automated Versioning and Tagging in CI](./python-project-5)

## 12. Project Requirements
(See individual project directories for full runnable code, setup, tests, and explanations.)

## 13. Progressive Difficulty
The projects start from a single file local commit (Project 1) to multi-branch scenarios (Project 2-3), introducing automation with hooks (Project 4) and finally integration with deployment workflows (Project 5).

## 14. Interview Preparation
- **Fundamental:** What is the difference between `git pull` and `git fetch`? (Fetch downloads data, pull downloads and merges).
- **Practical:** How do you undo the last commit without losing changes? (`git reset --soft HEAD~1`).
- **Debugging:** You accidentally committed a 500MB file a few commits ago. How do you remove it? (Interactive rebase or `git filter-repo`).
- **System Design:** How does Git scale to large monorepos? (Sparse checkout, VFS for Git, scalar).

## 15. Final Summary
- **Key Mental Models:** Git is a timeline of snapshots, not a list of file diffs.
- **Cheat Sheet:** `git init`, `git clone`, `git status`, `git add .`, `git commit -m`, `git push`, `git pull`, `git merge`, `git rebase`.
- **Common Mistakes:** Committing secrets, force pushing to main, forgetting to pull before pushing.
