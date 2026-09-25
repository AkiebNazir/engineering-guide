# Exercise 03: Handling Merge Conflicts 🟡

## 🎯 Objective
Deliberately create a merge conflict, understand why it happens, and resolve it confidently.

## 📋 Prerequisites
- Completed Exercises 01 and 02
- Understanding of branches and merging

## 📝 Instructions

### Step 1: Set Up the Scenario
```bash
mkdir conflict-practice && cd conflict-practice
git init

# Create initial file
cat > config.js << 'EOF'
const config = {
  appName: "TaskMaster",
  version: "1.0.0",
  port: 3000,
  database: "mongodb://localhost/taskmaster"
};
module.exports = config;
EOF

git add . && git commit -m "feat: add initial config"
```

### Step 2: Create Two Branches That Edit the Same Lines
```bash
# Branch A: Changes the port
git checkout -b feature/change-port
sed -i '' 's/port: 3000/port: 8080/' config.js   # macOS
# OR: sed -i 's/port: 3000/port: 8080/' config.js  # Linux
git add . && git commit -m "feat: change port to 8080"

# Branch B: Also changes the port (differently!)
git checkout main
git checkout -b feature/change-port-ssl
sed -i '' 's/port: 3000/port: 443/' config.js
git add . && git commit -m "feat: change port to 443 for SSL"
```

### Step 3: Trigger the Conflict
```bash
# Merge branch A into main
git checkout main
git merge feature/change-port    # ✅ This works fine

# Now try to merge branch B
git merge feature/change-port-ssl  # 💥 CONFLICT!
```

### Step 4: Examine the Conflict
```bash
git status   # Shows conflicted files
cat config.js
```

You'll see conflict markers:
```javascript
const config = {
  appName: "TaskMaster",
  version: "1.0.0",
<<<<<<< HEAD
  port: 8080,
=======
  port: 443,
>>>>>>> feature/change-port-ssl
  database: "mongodb://localhost/taskmaster"
};
```

### Step 5: Resolve the Conflict
Edit `config.js` — remove the conflict markers and choose the correct value:
```javascript
const config = {
  appName: "TaskMaster",
  version: "1.0.0",
  port: 8080,     // Decided: use 8080 for development
  sslPort: 443,   // Added: separate SSL port
  database: "mongodb://localhost/taskmaster"
};
module.exports = config;
```

### Step 6: Complete the Merge
```bash
git add config.js
git commit -m "merge: resolve port conflict, add separate SSL port"
git log --oneline --graph --all
```

### Questions to Answer
1. Why did the conflict happen?
2. What do `<<<<<<<`, `=======`, and `>>>>>>>` markers mean?
3. Could this conflict have been avoided? How?
4. How does this relate to CI/CD? (Hint: what if this happened in a pipeline?)

## ✅ Expected Output
A clean merge with both port values preserved and a merge commit in the history.

## 🧠 Key Takeaway
Merge conflicts are normal and not scary. In CI/CD, frequent integration (small, frequent merges) dramatically reduces the chance and complexity of conflicts.
