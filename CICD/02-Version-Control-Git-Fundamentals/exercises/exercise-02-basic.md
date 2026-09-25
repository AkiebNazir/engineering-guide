# Exercise 02: Branching & Merging Basics 🟢

## 🎯 Objective
Learn to create branches, switch between them, and merge changes.

## 📋 Prerequisites
- Completed Exercise 01 (have a Git repository)

## 📝 Instructions

### Step 1: Create and Switch to a Feature Branch
```bash
cd my-first-repo
git branch feature/greeting
git checkout feature/greeting
# OR: git checkout -b feature/greeting
```

### Step 2: Make Changes on the Feature Branch
```bash
cat > greet.js << 'EOF'
function greet(name) {
  return `Hello, ${name}! Welcome to CI/CD.`;
}
module.exports = greet;
EOF

git add greet.js
git commit -m "feat: add greeting function"
```

### Step 3: Make Another Commit on the Feature Branch
```bash
cat > greet.test.js << 'EOF'
const greet = require('./greet');
console.log(greet('World'));
// Expected: "Hello, World! Welcome to CI/CD."
EOF

git add greet.test.js
git commit -m "test: add greeting test"
```

### Step 4: Switch Back to Main and See the Difference
```bash
git checkout main
ls  # Notice: greet.js and greet.test.js are GONE!

git checkout feature/greeting
ls  # They're back!
```

### Step 5: Merge Feature into Main
```bash
git checkout main
git merge feature/greeting
git log --oneline --graph
```

### Step 6: Clean Up
```bash
git branch -d feature/greeting
git branch  # Verify it's deleted
```

## ✅ Expected Output
```
$ git log --oneline --graph
* abc1234 test: add greeting test
* def5678 feat: add greeting function
* b2c3d4e feat: add v2 output and gitignore
* a1b2c3d feat: initial project setup
```

## 🧠 Key Takeaway
Branches are lightweight and cheap in Git. They let you work on features in isolation without affecting the main codebase. This is what enables parallel development in CI/CD.
