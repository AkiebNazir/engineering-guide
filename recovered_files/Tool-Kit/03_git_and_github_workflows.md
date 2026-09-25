# Git and GitHub Workflows

Git is not just a tool for saving code; it is a distributed graph database. Understanding the underlying graph is the difference between blindly copy-pasting StackOverflow commands to fix conflicts and confidently rewriting history.

## 1. Git Internals: The Directed Acyclic Graph (DAG)

Git doesn't store diffs; it stores snapshots.

```arch
%% caption: Branches in Git are just lightweight, movable pointers to a specific commit hash in the DAG.
route straight
node head "HEAD" at 2,0 shape=pill color=red
node feat "feature" at 0,1 shape=pill color=green
node main "main" at 4,1 shape=pill color=blue

node c4 "Commit D" at 0,2 shape=circle color=slate
node c3 "Commit C" at 4,2 shape=circle color=slate
node c2 "Commit B" at 2,3 shape=circle color=slate
node c1 "Commit A" at 2,4 shape=circle color=slate

head -> feat
feat -> c4
main -> c3
c4 -> c2
c3 -> c2
c2 -> c1
```

- **Commit**: A snapshot of the entire repository at a moment in time, plus a pointer to its parent commit(s).
- **Branch**: A lightweight pointer (a text file containing a hash) to a commit.
- **HEAD**: A pointer to the branch (or commit) you currently have checked out in your working directory.

## 2. Rebase vs. Merge

When integrating a feature branch back into `main`, you have two structural choices.

### Merge
Creates a new "Merge Commit" that has two parents.
- **Pros**: Non-destructive, preserves exact history and chronology.
- **Cons**: Can create a messy "train track" history if dozens of developers are merging constantly.

### Rebase
Takes the commits from your feature branch, rewinds them, and replays them one-by-one on top of the latest `main`.
- **Pros**: Creates a perfectly linear, readable history.
- **Cons**: It *rewrites* history. The replayed commits have brand new hashes. **Never rebase commits that have already been pushed and shared with other developers**, or you will force them into a conflict nightmare.

*Production standard:* Fetch `main` and **rebase** your local feature branch on top of it to resolve conflicts locally, then open a PR, and use GitHub's **"Squash and Merge"** to turn the entire PR into a single commit on `main`.

## 3. The Escape Hatches

When things go wrong, you need these commands:

### `git reflog`
Git rarely deletes anything immediately. `git reflog` is a journal of every time your `HEAD` pointer moved. If you accidentally do a `git reset --hard` and lose your commits, you can look at the reflog, find the hash of where you were before the mistake, and simply `git reset --hard <that-hash>` to get it all back.

### `git cherry-pick <hash>`
You committed to the wrong branch, or you only want *one* specific commit from a dead branch. `cherry-pick` copies a single commit and applies it to your current branch.

### `git bisect`
You discover a bug on `main`, but you don't know which commit introduced it. `bisect` performs a binary search through history.
```bash
git bisect start
git bisect bad                 # the current commit is broken
git bisect good v1.0.0         # it was working in the last release
# Git will checkout a commit halfway between. You test it.
# You type `git bisect good` or `git bisect bad`.
# Git repeats until it pinpoints the exact commit that broke the code.
```

## 4. GitHub PRs and Code Review Best Practices

A Pull Request is a request for a conversation.
1. **Keep it small**: A PR with 50 lines gets heavily scrutinized. A PR with 2,000 lines gets a "LGTM 👍". Keep PRs under 400 lines of logic.
2. **Review yourself first**: Always read your own diff in the GitHub UI before requesting a review. You will catch 50% of your own mistakes just by seeing them in a different context.
3. **Branch Protection Rules**: A production repo should physically prevent anyone from pushing directly to `main`. Require at least 1 approving review, and require CI status checks (tests and linters) to pass before the merge button is enabled.

## 5. GitHub Actions (CI/CD)

GitHub Actions is a CI/CD runner built directly into the repo. You define workflows in `.github/workflows/`.

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
    - uses: actions/checkout@v3
    - name: Set up Go
      uses: actions/setup-go@v4
      with:
        go-version: '1.21'
    - name: Run Tests
      run: go test -v ./...
    - name: Lint
      uses: golangci/golangci-lint-action@v3
```

This workflow runs on every PR. Because of branch protection rules, the PR cannot be merged if `go test` fails. This is the foundation of automated quality control.
