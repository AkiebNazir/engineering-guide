# Exercise 05: Complete Git Workflow with Hooks and Protection 🔴

## 🎯 Objective
Set up a professional Git workflow with conventional commits enforced by hooks, branch protection simulation, and a multi-branch collaboration scenario.

## 📋 Prerequisites
- Node.js installed
- GitHub account
- All previous exercises completed

## 📝 Instructions

### Step 1: Create the Project

```bash
mkdir pro-git-workflow && cd pro-git-workflow
git init
npm init -y
```

### Step 2: Set Up Conventional Commit Enforcement

Install commit linting tools:
```bash
npm install --save-dev @commitlint/cli @commitlint/config-conventional husky
```

Create `commitlint.config.js`:
```javascript
module.exports = {
  extends: ['@commitlint/config-conventional'],
  rules: {
    'type-enum': [2, 'always', [
      'feat', 'fix', 'docs', 'style', 'refactor',
      'test', 'chore', 'ci', 'perf', 'revert'
    ]],
    'subject-max-length': [2, 'always', 72],
    'subject-empty': [2, 'never'],
  }
};
```

Set up Husky hooks:
```bash
npx husky init
echo "npx --no -- commitlint --edit \$1" > .husky/commit-msg
```

### Step 3: Add a Pre-commit Hook for Linting

Create a simple app with linting:
```bash
npm install --save-dev eslint
npx eslint --init  # Choose: problems, esm/commonjs, none, no, node
```

Add pre-commit hook:
```bash
echo "npx eslint ." > .husky/pre-commit
```

### Step 4: Build the Application

Create `src/calculator.js`:
```javascript
class Calculator {
  add(a, b) { return a + b; }
  subtract(a, b) { return a - b; }
  multiply(a, b) { return a * b; }
  divide(a, b) {
    if (b === 0) throw new Error('Division by zero');
    return a / b;
  }
}
module.exports = Calculator;
```

```bash
git add .
git commit -m "feat: initial project with calculator and git hooks"
```

Try a bad commit message:
```bash
echo "// test" >> src/calculator.js
git add .
git commit -m "stuff"  # ❌ Should be REJECTED by commitlint!
git commit -m "feat: add test comment"  # ✅ Should work
```

### Step 5: Simulate Team Collaboration

Simulate 3 developers working on different features:

**Developer A — Add history feature:**
```bash
git checkout -b feature/history
cat > src/history.js << 'EOF'
class CalculatorHistory {
  constructor() { this.history = []; }
  add(operation, result) {
    this.history.push({ operation, result, timestamp: new Date() });
  }
  getAll() { return this.history; }
  clear() { this.history = []; }
}
module.exports = CalculatorHistory;
EOF
git add . && git commit -m "feat(history): add calculation history tracking"
```

**Developer B — Add scientific functions:**
```bash
git checkout main
git checkout -b feature/scientific
cat > src/scientific.js << 'EOF'
class ScientificCalculator {
  sqrt(x) {
    if (x < 0) throw new Error('Cannot sqrt negative number');
    return Math.sqrt(x);
  }
  power(base, exp) { return Math.pow(base, exp); }
  log(x) {
    if (x <= 0) throw new Error('Log undefined for non-positive');
    return Math.log(x);
  }
}
module.exports = ScientificCalculator;
EOF
git add . && git commit -m "feat(scientific): add scientific calculator functions"
```

**Developer C — Update the main calculator (creates potential conflict):**
```bash
git checkout main
git checkout -b feature/calculator-v2
cat > src/calculator.js << 'EOF'
class Calculator {
  constructor() { this.lastResult = null; }
  add(a, b) { this.lastResult = a + b; return this.lastResult; }
  subtract(a, b) { this.lastResult = a - b; return this.lastResult; }
  multiply(a, b) { this.lastResult = a * b; return this.lastResult; }
  divide(a, b) {
    if (b === 0) throw new Error('Division by zero');
    this.lastResult = a / b;
    return this.lastResult;
  }
  getLastResult() { return this.lastResult; }
}
module.exports = Calculator;
EOF
git add . && git commit -m "feat(calc): add lastResult tracking to calculator"
```

### Step 6: Merge All Features (Resolve Conflicts)

```bash
git checkout main
git merge feature/history          # Clean merge ✅
git merge feature/scientific       # Clean merge ✅
git merge feature/calculator-v2    # Possible conflict! Resolve it.
```

### Step 7: Tag a Release

```bash
git tag -a v1.0.0 -m "Release 1.0.0: Calculator with history and scientific functions"
git log --oneline --graph --all --decorate
```

### Step 8: Push to GitHub

1. Create a new repo on GitHub
2. Push everything:
```bash
git remote add origin https://github.com/YOUR_USERNAME/pro-git-workflow.git
git push -u origin main --tags
git push origin feature/history feature/scientific feature/calculator-v2
```

3. On GitHub, set up branch protection rules for `main`:
   - Require pull request before merging
   - Require at least 1 approval
   - Require status checks to pass

### Step 9: Verify Everything Works

- [ ] Conventional commits are enforced (bad messages rejected)
- [ ] Pre-commit linting runs automatically
- [ ] All three features are merged into main
- [ ] Release tag v1.0.0 exists
- [ ] Branch protection is configured on GitHub
- [ ] All branches are pushed to remote

## ✅ Expected Output

```bash
$ git log --oneline --graph --all --decorate
*   Merge branch 'feature/calculator-v2'
|\
| * feat(calc): add lastResult tracking
* |   Merge branch 'feature/scientific'
|\ \
| * | feat(scientific): add scientific calculator
| |/
* | Merge branch 'feature/history'
|\|
| * feat(history): add calculation history tracking
|/
* feat: initial project with calculator and git hooks
```

A fully professional Git setup with enforced conventions, hooks, and protection.

## 🧠 Key Takeaway
Professional teams don't rely on discipline alone — they use automation (hooks, branch protection, linting) to enforce quality standards. This automation is the bridge between version control and CI/CD pipelines.
