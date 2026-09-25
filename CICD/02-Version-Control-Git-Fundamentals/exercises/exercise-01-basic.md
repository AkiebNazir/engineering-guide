# Exercise 01: Git Basics — Your First Repository 🟢

## 🎯 Objective
Create your first Git repository, make commits, and understand the basic Git workflow.

## 📋 Prerequisites
- Git installed (`git --version` to check)

## 📝 Instructions

### Step 1: Create a Project
```bash
mkdir my-first-repo
cd my-first-repo
git init
```

Verify the `.git` folder was created:
```bash
ls -la
```

### Step 2: Create Files and Make Your First Commit
```bash
echo "# My First Project" > README.md
echo "console.log('Hello World');" > app.js
git status          # See untracked files
git add README.md   # Stage one file
git status          # See staged vs unstaged
git add app.js      # Stage the other
git commit -m "feat: initial project setup"
```

### Step 3: Make More Changes
```bash
echo "console.log('Version 2');" >> app.js
echo "node_modules/" > .gitignore
git diff            # See what changed
git add .
git commit -m "feat: add v2 output and gitignore"
```

### Step 4: View Your History
```bash
git log --oneline
git log --oneline --graph --all
```

### Step 5: Answer These Questions
1. What does `git status` show before and after `git add`?
2. What does `git diff` show?
3. How many commits does your repo have?
4. What is the SHA hash of your first commit?

## ✅ Expected Output
```
$ git log --oneline
b2c3d4e feat: add v2 output and gitignore
a1b2c3d feat: initial project setup
```
(Your hashes will be different)

## 🧠 Key Takeaway
The core Git workflow is: **edit → stage → commit**. Understanding these three areas is the foundation of everything in Git.
