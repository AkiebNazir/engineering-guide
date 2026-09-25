# Git & GitHub Workflows

Welcome to the ultimate guide on Git and GitHub Workflows. Git is the most widely used version control system in the world. Whether you are a solo developer tracking your own changes or a senior engineer collaborating with hundreds of others on a massive open-source project, mastering Git is a non-negotiable skill.

This guide will take you from the very basics of tracking files to advanced, confident history rewriting and CI/CD automation.

---

## Interactive Examples

This module contains practical, interactive examples to solidify your understanding. You can find them in the `examples/` directory:
- [Basic Local Repo](examples/01_basic_local_repo)
- [Basic Gitignore](examples/02_basic_gitignore)
- [Intermediate Rebase Conflict](examples/03_intermediate_rebase_conflict)
- [Intermediate Bisect](examples/04_intermediate_bisect)
- [Advanced GitHub Actions CI/CD](examples/05_advanced_github_actions)

---

## 1. Ground Zero: What is Git?

At its core, Git is a **Distributed Version Control System (DVCS)**. 
*   **Version Control:** It tracks changes to files over time so you can recall specific versions later. It's an undo button for your entire project.
*   **Distributed:** Unlike older systems (like SVN) where there is one central server that holds the history, in Git, *every developer's computer has a full, independent copy of the entire repository history*. 

### The Three States
Git has three main states that your files can reside in. Understanding these is the key to understanding Git's workflow.

1.  **Working Directory:** The actual files you see on your computer's hard drive. You edit these files directly.
2.  **Staging Area (Index):** A holding area. When you finish editing a file, you "add" it to the staging area. This lets you group related changes together before saving them.
3.  **Git Directory (Repository):** Where Git permanently stores the metadata and object database (the `.git` folder). When you "commit", Git takes the files from the Staging Area and stores them permanently here.

```arch
node wk "Working Directory" at 0,0 icon=folder sub="Your Files"
node st "Staging Area" at 1,0 icon=file sub="Index"
node rp "Local Repository" at 2,0 icon=git-icon sub=".git directory"

wk -> st : "git add"
st -> rp : "git commit"
rp -> wk : "git checkout"
```

---

## 2. Essential Git Commands

### Starting a Repository
*   `git init`: Initializes a brand new, empty Git repository in the current folder.
*   `git clone <url>`: Downloads an existing repository from the internet (like GitHub) onto your machine.

### Tracking and Committing
*   `git status`: **The most important command.** It tells you exactly what state your files are in (modified, staged, untracked).
*   `git add <file>`: Moves a modified file to the Staging Area.
*   `git add .`: Adds *all* modified and new files in the current directory to the Staging Area.
*   `git commit -m "Fix login bug"`: Takes everything in the Staging Area and saves it permanently to the repository with a descriptive message.

> [!TIP]
> Try it yourself! Check out [examples/01_basic_local_repo](examples/01_basic_local_repo) to see a local repository in action.


### Viewing History
*   `git log`: Shows the chronological history of commits.
*   `git diff`: Shows the exact lines of code you changed in the Working Directory that haven't been staged yet.
*   `git diff --staged`: Shows the exact lines of code you've added to the Staging Area waiting to be committed.

---

## 3. Git Internals: The Directed Acyclic Graph (DAG)

Most beginners think of Git as a list of changes or diffs. **This is wrong.** Git stores snapshots.

Every time you commit, Git takes a picture of what all your files look like at that exact moment. It stores this snapshot and assigns it a unique 40-character SHA-1 hash (e.g., `a1b2c3d...`). 

Because every commit (except the first one) points back to its "parent" commit, the history forms a **Directed Acyclic Graph (DAG)**. 

### What is a Branch?
A branch in Git is *not* a copy of your files. It is simply a lightweight, movable text pointer to a specific commit hash. 

### What is HEAD?
`HEAD` is a special pointer that points to the branch (or commit) you currently have checked out in your Working Directory.

```arch
route straight
grid 80x90
node head "HEAD" at 0,0 shape=pill color=amber
node feat "feature-branch" at 0,1 shape=pill color=blue
node main "main" at 1,1 shape=pill color=blue

node c4 "Commit D" at 0,2 shape=circle color=slate
node c3 "Commit C" at 1,2 shape=circle color=slate
node c2 "Commit B" at 0.5,3 shape=circle color=slate
node c1 "Commit A" at 0.5,4 shape=circle color=slate

head -> feat
feat -> c4
main -> c3
c4 -> c2
c3 -> c2
c2 -> c1
```

---

## 4. Branching and Merging

When building a new feature or fixing a bug, you should never work directly on the `main` branch. You create an isolated branch.
*   `git branch feature-login`: Creates a new branch pointer.
*   `git switch feature-login`: Moves `HEAD` to that branch, updating your Working Directory.
*   `git switch -c feature-login`: Creates and switches to the branch in one command.

Once the feature is done, you need to integrate it back into `main`. You have three structural choices:

### 1. Merge (`git merge`)
```bash
git switch main
git merge feature-login
```
Takes the two diverging branches and ties them together by creating a new "Merge Commit" that has two parents.
*   **Pros:** Non-destructive. Preserves the exact history and chronological order of events.
*   **Cons:** If dozens of developers are merging constantly, the graph becomes a tangled, unreadable "train track" of merge commits.

### 2. Rebase (`git rebase`)
```bash
git switch feature-login
git fetch origin
git rebase origin/main
# If there are conflicts, fix them, then:
# git add .
# git rebase --continue
git push --force-with-lease
```
Takes the commits from your feature branch, temporarily sets them aside, moves your branch to the tip of `main`, and then replays your commits one-by-one on top.
*   **Pros:** Creates a perfectly linear, clean, and readable history.
*   **Cons:** It **rewrites history**. The replayed commits get brand new hashes. 
*   **GOLDEN RULE OF REBASING:** *Never* rebase commits that you have already pushed to a public repository and shared with other developers. It will cause a massive synchronization headache.

> [!TIP]
> Practice resolving a rebase conflict safely in [examples/03_intermediate_rebase_conflict](examples/03_intermediate_rebase_conflict).


### 3. Squash (GitHub "Squash and Merge")
Takes all the commits from your feature branch (even if it's 50 messy commits like "WIP", "Fix typo", "Actually fix bug"), combines them into one single, cohesive commit, and places it on `main`.
*   **Pros:** Keeps `main` incredibly clean. Every commit on `main` represents one fully completed feature or bug fix.

---

## 5. Working with Remotes (GitHub, GitLab)

A "remote" is simply another copy of your repository hosted on the internet or a network. By default, when you clone, Git names the remote server `origin`.

*   `git fetch`: Reaches out to `origin` and downloads all new data (commits, branches) that you don't have yet. **It does not modify your Working Directory.**
*   `git pull`: A combination command. It runs `git fetch`, and then immediately tries to `git merge` the downloaded changes into your current branch.
*   `git push`: Uploads your local commits to the remote repository.

---

## 6. The Escape Hatches (Advanced Git)

When things go wrong, these commands will save your life.

### 1. `git reflog` (The Time Machine)
Git rarely deletes anything immediately. The `reflog` is a journal of every single time your `HEAD` pointer moved. 
If you accidentally execute `git reset --hard` and completely wipe out a week of commits, don't panic. Run `git reflog`, find the hash of where you were before the mistake, and run `git reset --hard <that-hash>` to restore everything.

### 2. `git cherry-pick <hash>`
Imagine you committed a critical hotfix to a dead development branch by accident. You don't want to merge the whole branch, you just want that *one* commit. `cherry-pick` copies a single commit and applies it to your current branch.
```bash
# Find the hash of the commit you want (e.g., a1b2c3d)
git switch main
git cherry-pick a1b2c3d
```

### 3. `git bisect` (The Bug Hunter)
You discover a severe bug on `main`, but you don't know when it was introduced (it could have been anytime in the last 500 commits). `bisect` performs a binary search through history to find the exact commit that broke the code.
```bash
git bisect start
git bisect bad                 # Tell Git the current commit is broken
git bisect good v1.0.0         # Tell Git it was working in the v1.0 release

# Git will automatically checkout a commit exactly halfway between. 
# You run your tests. 
# If the test fails, you type: `git bisect bad`
# If the test passes, you type: `git bisect good`

# Git repeats the binary search until it pinpoints the exact offending commit!
```

> [!TIP]
> Hunt down a sneaky bug with binary search in [examples/04_intermediate_bisect](examples/04_intermediate_bisect).


### 4. `git stash`
You are halfway through a messy feature, and suddenly your boss asks you to fix a critical bug on `main`. You aren't ready to commit your messy code yet. 
`git stash` takes your modified tracked files and saves them on a stack of unfinished changes, leaving your Working Directory clean. After you fix the bug, you switch back and run `git stash pop` to reapply your messy code.

---

## 7. GitHub PRs and Code Review Best Practices

A Pull Request (PR) is a request for a conversation. It's where engineering culture happens.

1.  **Keep it small:** A PR with 50 lines gets heavily scrutinized. A PR with 2,000 lines gets a rubber-stamp "LGTM 👍" because nobody has the mental capacity to read it. Keep PRs under 400 lines of logic.
2.  **Review yourself first:** Always read your own diff in the GitHub UI before clicking "Request Review". You will catch 50% of your own mistakes just by seeing the code in a different context.
3.  **Branch Protection Rules:** A production repository should physically prevent anyone from pushing directly to `main`. You should require at least 1 approving review, and require CI status checks (tests, linters) to pass before the merge button turns green.

---

## 8. GitHub Actions (CI/CD)

GitHub Actions is a Continuous Integration and Continuous Deployment (CI/CD) runner built directly into your repository. You define automated workflows in YAML files inside the `.github/workflows/` directory.

### Example: Automated Testing Workflow
```yaml
name: CI
on:
  push:
    branches: [ "main" ]
  pull_request:
    branches: [ "main" ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - name: Checkout Code
      uses: actions/checkout@v3
    
    - name: Set up Go
      uses: actions/setup-go@v4
      with:
        go-version: '1.21'
        
    - name: Run Tests
      run: go test -v ./...
      
    - name: Lint
      uses: golangci/golangci-lint-action@v3
```

**How it works:** 
Every time a developer opens a PR targeting `main`, GitHub spins up a fresh Ubuntu Linux server (`runs-on: ubuntu-latest`), clones the code, installs Go, runs the test suite, and runs the linter. 
Because of Branch Protection Rules, if `go test` fails, the workflow fails, and the developer is blocked from merging the broken code into `main`. This is the absolute foundation of automated quality control.

> [!TIP]
> Explore a production-grade CI/CD setup in [examples/05_advanced_github_actions](examples/05_advanced_github_actions).


---

## 9. Interview Questions

### 1. What is the difference between `git merge` and `git rebase`?
**Answer:** Both integrate changes from one branch into another, but they do it differently. `git merge` creates a new "merge commit" that ties the histories together, preserving the exact chronological history of both branches. `git rebase` rewinds the commits on your current branch, moves the branch pointer to the tip of the target branch, and replays your commits sequentially on top. Rebase creates a cleaner, perfectly linear history, but it rewrites commit hashes, making it dangerous to use on public, shared branches.

### 2. How do you undo a commit that you have already pushed to a remote repository?
**Answer:** Because the commit is already public, you should *not* rewrite history using `git reset` or `git rebase`. Instead, you should use `git revert <commit-hash>`. This creates a brand new commit that perfectly inverts the changes of the bad commit (e.g., deleting the lines the bad commit added). This preserves history and safely synchronizes with other developers.

### 3. What is the difference between `git fetch` and `git pull`?
**Answer:** `git fetch` safely reaches out to the remote repository and downloads all the latest commits and branch metadata to your local `.git` directory, but it *does not* touch your Working Directory. `git pull` is a combination command: it runs `git fetch`, and then immediately attempts to run `git merge` to integrate the downloaded changes into your current Working Directory. 

### 4. You realize your last commit had a typo in the commit message, or you forgot to stage a file. How do you fix it?
**Answer:** If you haven't pushed the commit yet, you can stage the forgotten file (`git add <file>`) and then run `git commit --amend`. This will open your editor to let you fix the message, and it will rewrite the previous commit to include the new file and the new message, rather than creating a second commit.

### 5. Explain what a "detached HEAD" state is.
**Answer:** Normally, the `HEAD` pointer points to a branch name (like `main`), and the branch name points to a commit hash. If you checkout a specific commit hash directly (e.g., `git checkout a1b2c3d`), `HEAD` detaches from the branch and points directly to the commit. You can view the code as it was at that exact moment. However, if you make new commits in a detached HEAD state, they won't belong to any branch, and they will be lost (garbage collected) as soon as you checkout a branch again, unless you create a new branch to hold them.

### 6. What is the purpose of the `.gitignore` file?
**Answer:** It tells Git which files or directories should be intentionally untracked and completely ignored by Git. This is crucial for keeping the repository clean and secure. You use it to ignore build artifacts (like `node_modules/` or compiled `.class` files), OS-specific hidden files (like `.DS_Store`), and critically, local configuration files containing sensitive secrets or API keys (like `.env`).

> [!TIP]
> See a robust, production-ready `.gitignore` in [examples/02_basic_gitignore](examples/02_basic_gitignore).


### 7. Describe a Git workflow for a team of 10 developers.
**Answer:** A standard approach is GitHub Flow (or trunk-based development). The `main` branch is always deployable and protected. When a developer wants to build a feature, they create a feature branch off `main` (e.g., `feat/login`). They commit their work locally, push the branch to the remote, and open a Pull Request (PR) against `main`. Automated CI/CD pipelines run tests on the PR. Other developers review the code. Once approved and tests pass, the PR is "Squash and Merged" into `main`, keeping the `main` history linear and clean.
