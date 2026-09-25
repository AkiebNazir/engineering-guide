# Exercise 04: Rebase vs Merge — See the Difference 🟡

## 🎯 Objective
Perform both a merge and a rebase on identical scenarios to visually see the difference in commit history.

## 📋 Prerequisites
- Understanding of branches and merging from previous exercises

## 📝 Instructions

### Setup: Create Two Identical Repos

```bash
# Repo 1: For merge
mkdir merge-demo && cd merge-demo && git init
echo "Line 1" > file.txt && git add . && git commit -m "commit 1"
echo "Line 2" >> file.txt && git add . && git commit -m "commit 2"

# Create feature branch and add commits
git checkout -b feature/widget
echo "Widget A" > widget.txt && git add . && git commit -m "feat: add widget A"
echo "Widget B" >> widget.txt && git add . && git commit -m "feat: add widget B"

# Add a commit to main while feature branch exists
git checkout main
echo "Line 3" >> file.txt && git add . && git commit -m "commit 3 on main"

cd ..

# Repo 2: Exact same setup for rebase
cp -r merge-demo rebase-demo
```

### Part A: The Merge Approach
```bash
cd merge-demo
git checkout main
git merge feature/widget -m "merge: integrate widget feature"
git log --oneline --graph --all
```

### Part B: The Rebase Approach
```bash
cd ../rebase-demo
git checkout feature/widget
git rebase main              # Replay feature commits on top of main
git checkout main
git merge feature/widget     # Fast-forward merge (no merge commit!)
git log --oneline --graph --all
```

### Part C: Compare the Histories

Draw or write out the commit graphs for both approaches:

**Merge Result:**
```
*   merge commit
|\
| * feat: add widget B
| * feat: add widget A
* | commit 3 on main
|/
* commit 2
* commit 1
```

**Rebase Result:**
```
* feat: add widget B
* feat: add widget A
* commit 3 on main
* commit 2
* commit 1
```

### Questions to Answer
1. Which approach has a cleaner history?
2. Which approach shows WHEN the feature was developed in parallel?
3. When would you prefer merge over rebase?
4. What is a "fast-forward merge"?
5. If three developers used rebase and all pushed at the same time, what could go wrong?

## ✅ Expected Output
Two repos with identical code but different commit histories. You should clearly see the merge commit in the merge approach and the linear history in the rebase approach.

## 🧠 Key Takeaway
Merge preserves the branching history (good for auditing). Rebase creates a clean, linear history (good for readability). Most CI/CD teams use **squash-and-merge** on PRs — which combines the best of both worlds.
