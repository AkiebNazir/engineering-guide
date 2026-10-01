# Git and GitHub Workflows

Git is not just a tool for saving code; it is a small content-addressed database of
snapshots linked into a directed acyclic graph (DAG), plus a handful of movable pointers
into that graph. Once you see the graph, the commands stop being magic spells: merge,
rebase, reset, cherry-pick and reflog are all "add nodes" or "move a pointer". This
chapter builds that model from zero, then covers what teams and interviewers expect in
practice: branching and integration strategies, recovering from mistakes, pull requests
and code review, repository protection, GitHub Actions, and working with large repos.

## Foundations — What is version control, and what is Git doing?

### The problem

Without version control, a team shares code by copying folders: `api_final_v2_REAL.zip`.
Nobody knows which copy is current, two people overwrite each other's changes, and when a
bug appears nobody can say what changed since last week. Version control fixes three
things: **history** (every change is recorded with who, when and why), **collaboration**
(many people change the same code base and combine their work), and **safety** (any past
state can be restored).

Older systems (CVS, Subversion) kept the history on one central server. **Git** (written
by Linus Torvalds in 2005 for Linux kernel development) is **distributed**: every clone
is a full copy of the entire history. You commit, branch, diff and search history
offline; a "remote" such as GitHub is just another copy that the team agrees to treat as
the shared one.

### The pieces

| Piece | What it is | Everyday analogy |
|---|---|---|
| **Repository** | The `.git` directory: all objects (snapshots) and refs (pointers) | A photo album with every version of the project |
| **Working tree** | The files you edit | The desk you're working on |
| **Index / staging area** | The snapshot you are preparing for the next commit | The photo you're framing before gluing it into the album |
| **Commit** | An immutable snapshot of the whole project, plus author, message and parent commit(s) | One page in the album, with a caption and "continues from page 41" |
| **Branch** | A movable name pointing at one commit | A bookmark |
| **HEAD** | Which branch (or commit) you currently have checked out | "You are here" |
| **Remote** | Another copy of the repository you fetch from and push to (`origin`) | A friend's copy of the album that you sync with |
| **Pull request (PR)** | A GitHub request to merge one branch into another, with review and CI | Asking the editor to add your pages |

### The everyday loop

```bash
git switch -c fix-rounding          # new branch from where you are
# edit files
git add -p                          # stage the hunks you mean to commit, reviewing each
git commit -m "Round totals half-even to match the ledger"
git push -u origin fix-rounding     # publish the branch; open a PR on GitHub
# review, CI green → merge on GitHub
git switch main && git pull         # bring your local main up to date
```

```arch
%% caption: Changes move from the working tree to the index to local history, then to the shared remote; fetch brings others' history back.
grid 170x100
group local "Your machine" color=blue icon=desktop
node wt "Working tree" at 0,0 in local icon=edit sub="files you edit"
node idx "Index" at 1,0 in local icon=layers sub="next snapshot"
node repo "Local repo" at 2,0 in local icon=git-icon sub=".git objects + refs"
node remote "origin (GitHub)" at 2,2 icon=github-icon sub="shared copy"
wt -> idx : "add"
idx -> repo : "commit"
repo -> remote : "push"
remote ..> repo : "fetch"
repo ..> wt : "switch / restore"
```

## 1. The object model: four kinds of object, addressed by hash

Everything Git stores is one of four object types, each named by the hash of its content:

| Object | Contains | Example |
|---|---|---|
| **blob** | The bytes of one file, with no name and no permissions | the contents of `main.go` |
| **tree** | A directory listing: mode, name and the hash of each blob or sub-tree | `src/` → `main.go` → blob `a1b2…` |
| **commit** | One root tree hash, parent commit hash(es), author, committer, timestamps, message | "Round totals half-even" |
| **annotated tag** | A pointer to an object with a tagger, message and optional signature | `v1.4.0` |

```arch
%% caption: A commit points to one root tree and to its parent; trees point to blobs and sub-trees. Unchanged files are shared, not copied.
grid 160x95
node c2 "commit 7e1d" at 0,0 icon=git-icon sub="Round half-even"
node c1 "commit 3a9f" at 2,0 icon=git-icon sub="Add totals"
node t2 "tree (root)" at 0,1 icon=folder
node t1 "tree (root)" at 2,1 icon=folder
node src2 "tree src/" at 0,2 icon=folder
node readme "blob README" at 1,2 icon=file sub="shared by both"
node b2 "blob main.go v2" at 0,3 icon=file
node b1 "blob main.go v1" at 2,3 icon=file
node src1 "tree src/" at 2,2 icon=folder
c2 -> c1 : "parent"
c2 -> t2
c1 -> t1
t2 -> src2
t2 -> readme
t1 -> readme
t1 -> src1
src2 -> b2
src1 -> b1
```

Consequences worth knowing:

- **A commit is a snapshot, not a diff.** `git show` computes the diff between a commit's
  tree and its parent's on the fly. **Precision note:** on disk, Git *does* use deltas:
  `git gc` packs objects into **packfiles**, where similar objects are delta-compressed
  against each other. Logically snapshots, physically compressed.
- **Identical content is stored once.** Ten commits that don't touch `README` all point to
  the same blob.
- **History is tamper-evident.** A commit hash covers its tree and its parent hash, so
  changing anything in the past changes every descendant's hash. That is why rebasing
  "rewrites history": it has to create new commits.
- **Hash function:** SHA-1 by default (hardened against the known collision attack since
  Git 2.13). Repositories can be created with SHA-256 (`git init --object-format=sha256`),
  and the Git project plans to make SHA-256 the default in Git 3.0; hosting support is
  still catching up.

You can compute a blob's name yourself. It is the SHA-1 of a header `blob <size>\0`
followed by the content:

```python
import hashlib
import subprocess

def git_blob_hash(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode()
    return hashlib.sha1(header + data).hexdigest()

content = b"hello\n"
print(git_blob_hash(content))  # ce013625030ba8dba906f756967f9e9ca394464a

try:  # cross-check with git itself, if it is installed
    out = subprocess.run(["git", "hash-object", "--stdin"], input=content,
                         capture_output=True, check=True).stdout.decode().strip()
    print("git agrees:", out == git_blob_hash(content))
except (FileNotFoundError, subprocess.CalledProcessError):
    pass
```

Explore a real repository with the plumbing commands:

```bash
git cat-file -p HEAD            # the commit: tree, parent, author, message
git cat-file -p 'HEAD^{tree}'   # the root tree listing
git rev-parse HEAD~3            # hash of the great-grandparent
git count-objects -vH           # loose vs packed objects and sizes
```

## 2. Refs, HEAD and the three trees

A **ref** is a name for a commit hash: branches live in `refs/heads/`, remote-tracking
branches in `refs/remotes/origin/`, tags in `refs/tags/` (loose files or the
`packed-refs` file). A branch is literally a 41-byte file containing a hash. Creating a
branch costs nothing, and committing on a branch just moves that pointer to the new
commit.

`HEAD` normally points at a branch (`ref: refs/heads/main`). If you check out a commit or
tag directly, HEAD points at the commit itself: **detached HEAD**. Commits made there
belong to no branch and become unreachable when you switch away (the reflog still
remembers them for a while; create a branch with `git switch -c rescue` to keep them).

### The three trees and what `reset` does

Git juggles three versions of your files: **HEAD** (the last commit), the **index**
(staged), and the **working tree**. Most confusing commands are just "copy between these".

| Command | Moves the branch | Resets the index | Resets the working tree | Typical use |
|---|---|---|---|---|
| `git reset --soft <c>` | yes | no | no | Squash the last few commits into one (`reset --soft HEAD~3 && commit`) |
| `git reset [--mixed] <c>` | yes | yes | no | Un-commit and un-stage, keep the edits |
| `git reset --hard <c>` | yes | yes | yes | Throw away commits *and* uncommitted edits (uncommitted work is not recoverable) |
| `git restore --staged f` | no | yes (for `f`) | no | Unstage a file |
| `git restore f` | no | no | yes (for `f`) | Discard edits to a file |
| `git switch <branch>` | moves HEAD | yes | yes | Change branches (keeps local edits if they don't conflict) |

`git switch` and `git restore` (Git 2.23+) split the overloaded `git checkout` into two
clear commands. `checkout` still works.

## 3. Integrating work: fast-forward, merge, rebase, squash

```arch
%% caption: main and feature diverged at B. A merge adds a commit with two parents; a rebase replays D as a new commit D' on top of C.
route straight
grid 110x80
node head "HEAD" at 0,0 shape=pill color=red
node feat "feature" at 0,1 shape=pill color=green
node mainr "main" at 3,1 shape=pill color=blue
node d "D" at 0,2 shape=circle color=green
node c "C" at 3,2 shape=circle color=blue
node b "B" at 1.5,3 shape=circle color=slate
node a "A" at 1.5,4 shape=circle color=slate
head -> feat
feat -> d
mainr -> c
d -> b
c -> b
b -> a
```

Arrows point from a commit to its parent, and from a ref to its commit. The **merge
base** of `feature` and `main` is `B`, their most recent common ancestor.

### Fast-forward

If `main` has not moved since you branched, merging `feature` into `main` just moves the
`main` pointer forward. No new commit. `git merge --ff-only` refuses anything else,
which is a good default for `git pull` (`git config --global pull.ff only`).

### Three-way merge

When both sides have new commits, Git compares each side with the merge base and
combines the changes, creating a **merge commit** with two parents. Git's default merge
strategy has been `ort` since Git 2.34 (it replaced `recursive`). A **conflict** means both
sides changed the same lines (or one deleted a file the other edited); Git writes
conflict markers, you edit, `git add`, and `git merge --continue`. `git config --global
merge.conflictStyle zdiff3` shows the base version inside the markers, which makes most
conflicts obvious.

- **Pros:** non-destructive; records exactly what happened, including when branches joined.
- **Cons:** long-lived busy repositories get a tangled "train track" history.

### Rebase

`git rebase main` (on `feature`) takes the commits unique to `feature` (`D`), and replays
them one by one on top of `main`'s tip, producing new commits (`D'`) with new hashes,
then moves `feature` to point at them.

- **Pros:** linear, readable history; conflicts are resolved commit by commit against the
  latest code.
- **Cons:** it creates new commits. **Never rebase commits other people have based work
  on** (a shared branch), or their copies diverge from yours. Rebasing your own
  unmerged PR branch is normal; push it with `git push --force-with-lease`, which refuses
  if the remote has commits you haven't seen (plain `--force` would silently delete them).

**Interactive rebase** (`git rebase -i HEAD~5`) edits your local history before you
share it: reorder, `squash`/`fixup` commits together, `reword` messages, `drop` a commit,
`edit` to split one. `git commit --fixup <sha>` plus `git rebase -i --autosquash` is the
tidy way to address review comments.

### Squash merge

GitHub's **Squash and merge** turns the whole PR into one commit on `main`. You get one
commit per PR (easy to revert, easy to read), at the cost of losing the PR's internal
commits from `main`'s history (they remain on the PR page).

| Strategy on GitHub | `main` history | Revert a PR | Good for |
|---|---|---|---|
| Merge commit | All commits + merge commits | `git revert -m 1 <merge>` | Preserving detail; release branches |
| Squash and merge | One commit per PR, linear | `git revert <sha>` | Most product teams |
| Rebase and merge | PR's commits replayed, linear | Revert each commit | Teams that curate commits carefully |

A common production standard: rebase your branch on the latest `main` locally to resolve
conflicts, open a PR, squash-merge when CI is green and review is approved.

## 4. Remotes: fetch, pull, push

- `git fetch` downloads new objects and updates remote-tracking refs
  (`origin/main`). It never changes your branches or files. Always safe.
- `git pull` = `fetch` + integrate into the current branch (merge by default, or rebase
  with `--rebase` / `pull.rebase true`).
- `git push` uploads your commits and asks the remote to move its branch; it is rejected
  as **non-fast-forward** if the remote has commits you don't. Fetch and integrate, then
  push again.
- An upstream (tracking) branch lets `git status` say "ahead 2, behind 1".

```bash
git fetch --prune                      # also delete remote-tracking refs for branches deleted on the server
git log --oneline --graph main..origin/main   # what others pushed that I don't have
git log --oneline origin/main..main           # what I have that isn't pushed
git push --force-with-lease            # after rebasing your own PR branch
```

## 5. The escape hatches

### `git reflog`: undo almost anything

Every time HEAD or a branch moves, Git appends an entry to the **reflog** (kept ≈ 90 days
by default for reachable entries, 30 for unreachable ones). A bad `reset --hard`, a
botched rebase, a deleted branch: find the entry before the mistake and point a branch
back at it.

```bash
git reflog                                # HEAD@{0}: rebase (finish) … HEAD@{5}: commit: add retries
git branch rescue HEAD@{5}                # or: git reset --hard HEAD@{5}
git reset --hard ORIG_HEAD                # undo the last merge/rebase/reset: ORIG_HEAD is set before them
```

Limits: the reflog is **local** (a fresh clone has none) and it only covers committed
work. Uncommitted changes discarded by `reset --hard` or `restore` are gone (staged ones
may survive as dangling blobs: `git fsck --lost-found`).

### `git revert`: undo on a shared branch

`git revert <sha>` creates a new commit that applies the inverse change. It is the
correct way to undo something already on `main`, because it doesn't rewrite shared
history.

### `git cherry-pick <sha>`

Copies a single commit onto the current branch (new hash, same change). Used for
backporting a fix to a release branch, or rescuing one commit from an abandoned branch.
Add `-x` to record the original hash in the message.

### `git stash`

Shelves uncommitted changes so you can switch context: `git stash push -m "wip"`,
`git stash list`, `git stash pop`. For longer interruptions, `git worktree add
../hotfix main` gives you a second working tree on another branch from the same
repository, with no stashing needed.

### `git bisect`: binary search for the commit that broke it

```bash
git bisect start
git bisect bad                  # current commit is broken
git bisect good v1.0.0          # this release was fine
# Git checks out the midpoint; test, then mark it:
git bisect good                 # or: git bisect bad
# … about log2(N) steps later Git names the first bad commit
git bisect reset
```

Automate it with a script that exits 0 for good, 1–127 (except 125) for bad, and 125 for
"can't test this commit, skip": `git bisect run ./scripts/repro.sh`. With 1,000 commits
between good and bad, that's ≈ 10 test runs.

### Other diagnostics

`git blame -w -C file` (who last changed each line, ignoring whitespace and following
moved code; add a `.git-blame-ignore-revs` file to skip mass-reformat commits),
`git log -S 'retryCount'` (commits that added or removed that string), `git log -p --follow
path`, `git diff main...feature` (three dots: changes on `feature` since the merge base,
which is what a PR shows).

## 6. Branching strategies

| Strategy | How it works | Fits |
|---|---|---|
| **Trunk-based development** | Everyone integrates small changes into `main` at least daily; short-lived branches (hours to a couple of days); unfinished work hidden behind feature flags; release from `main` | Continuous delivery, most SaaS teams; the DORA research associates it with higher delivery performance |
| **GitHub flow** | Branch from `main`, PR, review, merge, deploy `main` | The same idea with PRs; the common default |
| **GitFlow** | Long-lived `develop` and `main`, plus feature, release and hotfix branches | Versioned software with scheduled releases and several supported versions; heavy for web services |
| **Release branches** | `main` plus `release/1.4` cut at release time; fixes cherry-picked back | Mobile apps, on-prem software, anything with multiple versions in the field |

Long-lived branches are where merge pain comes from: the longer a branch lives, the
larger and riskier the eventual integration. See [Feature Flags and Rollbacks](../CICD/05_feature_flags_and_rollbacks.md)
for how flags make trunk-based development safe.

**Merge queues.** On a busy repo, two PRs can each pass CI against an old `main` and
break it together. GitHub's merge queue tests each PR on top of `main` plus the PRs ahead
of it in the queue, and only merges what passes in that combination.

## 7. Pull requests and code review

A pull request is a request for a conversation, not a formality.

1. **Keep it small.** Review quality drops sharply with size: a 50-line PR gets real
   scrutiny, a 2,000-line PR gets a skim and an approval. A common guideline is under ≈ 400
   changed lines of logic; split refactors from behavior changes, and use stacked PRs for
   large features.
2. **Describe the why.** The description should say what problem it solves, how it was
   tested, the risk and the rollback plan. Link the issue.
3. **Review yourself first.** Read your own diff in the GitHub UI before requesting review.
4. **As a reviewer,** look for correctness, tests, readability, security and operability
   (logging, metrics, failure handling) before style; let formatters and linters handle
   style. Mark nits as nits. Approve when it improves the code base, even if it isn't how
   you would have written it.
5. **Commit messages** explain *why*: a short imperative subject line (≈ 50 characters),
   a blank line, then a body. Many teams use Conventional Commits (`fix(api): …`,
   `feat: …`) so changelogs and version bumps can be generated.

### Protecting `main`

Configure **rulesets** (or the older branch protection rules) so that `main`:

- cannot be pushed to directly, force-pushed or deleted;
- requires a PR with at least one approval, and dismisses stale approvals on new commits;
- requires specific **status checks** (tests, lint, security scans) to pass;
- requires review from **CODEOWNERS** for the paths they own;
- optionally requires signed commits, linear history, and the merge queue.

```text
# .github/CODEOWNERS: the last matching pattern wins
*                    @acme/backend
/infra/              @acme/platform
/payments/           @acme/payments @acme/security
*.proto              @acme/api-review
```

Commit signing (GPG, SSH keys, or keyless with Sigstore's gitsign) proves a commit came
from a key you control; GitHub shows "Verified". Pushing secrets is blocked by GitHub
**push protection** (secret scanning) when enabled.

## 8. GitHub Actions: CI/CD inside the repository

A **workflow** (`.github/workflows/*.yml`) runs on **events** (push, pull_request,
schedule, workflow_dispatch, release…). It contains **jobs**, which run in parallel by
default on **runners** (GitHub-hosted VMs or your own self-hosted machines); each job is
a sequence of **steps** that either run shell commands or use a reusable **action**.

```yaml
name: CI
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

permissions:
  contents: read                    # least privilege for the GITHUB_TOKEN

concurrency:                        # cancel superseded runs on the same branch
  group: ci-${{ github.ref }}
  cancel-in-progress: true

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        go: ["1.25", "1.26"]
    steps:
      - uses: actions/checkout@v5
      - uses: actions/setup-go@v5
        with:
          go-version: ${{ matrix.go }}
          cache: true               # caches the module and build cache keyed on go.sum
      - run: go test -race -count=1 ./...

  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: actions/setup-go@v5
        with:
          go-version-file: go.mod
      - uses: golangci/golangci-lint-action@v8
        with:
          version: latest
```

With branch protection requiring `test` and `lint`, the PR cannot merge while either
fails. That is the foundation of automated quality control; the deeper CI design
(pipeline stages, caching, flaky tests) is in [Continuous Integration (CI) Fundamentals](../CICD/01_ci_fundamentals.md).

### Actions security essentials

| Risk | Mitigation |
|---|---|
| A third-party action is compromised (as happened to `tj-actions/changed-files` in March 2025) | Pin third-party actions to a full commit SHA, not a tag: `uses: owner/action@<40-char-sha> # v4.2.0`; let Dependabot update the pins |
| Over-privileged `GITHUB_TOKEN` | Top-level `permissions: contents: read`, grant more per job |
| Long-lived cloud keys in secrets | **OIDC**: `permissions: id-token: write`, and the cloud trusts GitHub's token for this repo and branch (e.g. `aws-actions/configure-aws-credentials` with `role-to-assume`) |
| `pull_request_target` running untrusted fork code with secrets | Avoid it, or never check out the PR head in it |
| Script injection via `${{ github.event.pull_request.title }}` inside `run:` | Pass untrusted values through `env:` and quote them in the shell |
| Secrets in logs | They are masked, but derived values aren't; don't echo them |

Other features you will use: reusable workflows (`workflow_call`), environments with
required reviewers for production deploys, `actions/cache` and artifacts, and larger or
ARM runners.

## 9. Large repositories and monorepos

| Problem | Tool |
|---|---|
| Clone of a big history is slow | **Partial clone**: `git clone --filter=blob:none` fetches blobs on demand; `--depth=1` shallow clones for CI |
| Checkout of a huge tree is slow | `git sparse-checkout set services/checkout libs/common` (cone mode) |
| Large binaries bloat history | **Git LFS** stores pointers in Git and the files on a separate server |
| Commands get slow over time | `git maintenance start` schedules background gc, commit-graph and prefetch; `core.fsmonitor` for status |
| Building only what changed | Monorepo build tools (Bazel, Nx, Turborepo, Pants) and path filters in CI |

Google's own monorepo runs on Piper, not Git, but the ideas (one version of every
dependency, atomic cross-project changes, CI that tests only affected targets) are what
Git monorepos imitate.

## 10. When a secret gets committed

1. **Rotate the secret immediately.** Assume it is compromised the moment it was pushed;
   bots scrape public GitHub within minutes. Rewriting history does not un-leak it.
2. Remove it from history if needed: `git filter-repo --replace-text expressions.txt`
   (the recommended replacement for `git filter-branch`) or BFG, then force-push and have
   everyone re-clone. Forks, clones and cached PR refs may still hold it, which is why
   step 1 comes first.
3. Prevent recurrence: push protection, a pre-commit secret scanner (gitleaks), and
   secrets loaded from a manager instead of files ([Secret Management](11_secret_management.md)).

## Common interview questions

**"What is the difference between merge and rebase? When would you use each?"**
Merge combines two lines of history with a merge commit that has two parents, preserving
history exactly. Rebase replays your commits on top of another branch, creating new
commits and a linear history. Rebase your own unshared branch to stay current; never
rebase commits others have built on; merge (or squash-merge) into `main`.

**"What exactly is a branch?"**
A ref: a file holding one commit hash. Committing moves it forward. That's why branching
is instant and why deleting a branch doesn't delete commits (they stay reachable from
other refs or the reflog until garbage collection).

**"Does Git store diffs or snapshots?"**
Logically snapshots: each commit points to a full tree. Physically, packfiles
delta-compress similar objects, so storage is efficient.

**"I ran `git reset --hard` and lost my commits. Can you recover them?"**
Yes, if they were committed: `git reflog`, find the entry before the reset, `git reset
--hard HEAD@{n}` or create a branch there. Uncommitted work in the working tree is gone.

**"How do you undo a commit that's already on main?"**
`git revert <sha>` (add `-m 1` for a merge commit), through a PR. Don't reset and
force-push a shared branch.

**"How would you find which commit introduced a regression?"**
`git bisect` with a known good and bad commit, ideally `git bisect run` with an automated
repro script; it takes about log2(N) steps.

**"What's `--force-with-lease` and why prefer it?"**
It force-pushes only if the remote branch is still where your last fetch saw it, so you
can't silently overwrite someone else's commits.

**"Trunk-based development vs GitFlow?"**
Trunk-based: small changes merged to `main` daily behind feature flags, with continuous
delivery. GitFlow: long-lived develop/release branches for scheduled, versioned releases.
Trunk-based reduces integration pain and suits services; GitFlow or release branches suit
software with several versions in the field.

**"How do you secure a CI workflow?"**
Least-privilege `GITHUB_TOKEN`, pin third-party actions to SHAs, OIDC instead of stored
cloud keys, protected environments for deploys, and treat PR titles, branch names and fork
code as untrusted input.

## What Each Engineering Level Should Know

| Level | Industry title | Google ladder | What they should know |
|---|---|---|---|
| Student/Intern | Intern | — | Clone, branch, add, commit, push, pull, open a PR; resolve a simple conflict; write a clear commit message |
| Junior (L3) | Software Engineer I / New grad | L3 | Rebase a PR branch and force-push with lease, interactive rebase to clean up, stash, revert, cherry-pick; recover with reflog; small, well-described PRs; read a CI failure |
| Mid (L4) | Software Engineer II | L4 | Explain the object model and refs, the three trees and `reset` modes; bisect with a script; write GitHub Actions workflows with caching and matrices; review others' code constructively |
| Senior (L5) | Senior Software Engineer | L5 | Choose the team's branching and merge strategy, set up rulesets, CODEOWNERS, required checks and merge queues; secure CI (SHA pinning, OIDC, least-privilege tokens); handle a leaked secret end to end |
| Staff+ (L6+) | Staff / Principal Engineer | L6–L7 | Set org-wide source-control and CI policy: monorepo vs polyrepo, build tooling for scale, supply-chain provenance for commits and builds, review culture and metrics (DORA), migration plans across hundreds of repositories |

## Interview checklist

- [ ] I can name the four object types and explain how a commit, tree and blob link together.
- [ ] I can explain why commits are snapshots logically and deltas physically.
- [ ] I can explain branches, HEAD, detached HEAD and remote-tracking branches as refs.
- [ ] I can say what `reset --soft`, `--mixed` and `--hard` each change.
- [ ] I can explain fast-forward, three-way merge, merge base, rebase and squash merge, and when to use each.
- [ ] I know why not to rebase shared history and why `--force-with-lease` beats `--force`.
- [ ] I can recover lost commits with the reflog and undo a merged change with `revert`.
- [ ] I can run `git bisect`, including `git bisect run`.
- [ ] I can compare trunk-based development, GitHub flow and GitFlow.
- [ ] I can list the rules that protect `main` and what CODEOWNERS and merge queues do.
- [ ] I can write a GitHub Actions workflow and name five ways to secure it.
- [ ] I know the right order of operations when a secret is committed.

Related: [Continuous Integration (CI) Fundamentals](../CICD/01_ci_fundamentals.md) (CI pipeline design), [GitOps and Argo CD](../CICD/04_gitops_and_argocd.md)
(Git as the source of truth for deployments), [Feature Flags and Rollbacks](../CICD/05_feature_flags_and_rollbacks.md)
(the flags trunk-based development depends on), [Secret Management](11_secret_management.md).
