# Exercise 05: Build Your First CI/CD Pipeline 🔴

## 🎯 Objective

Set up a complete, working CI/CD pipeline from scratch — a real GitHub repository with GitHub Actions that builds, tests, and deploys a simple application.

## 📋 Prerequisites
- A GitHub account
- Git installed on your machine
- Node.js installed (v18+)
- Basic terminal/command-line knowledge

## 📝 Instructions

### Step 1: Create a Simple Node.js Application

Create a new directory and initialize a project:

```bash
mkdir taskmaster-demo
cd taskmaster-demo
npm init -y
```

Create `index.js`:
```javascript
function add(a, b) {
  return a + b;
}

function subtract(a, b) {
  return a - b;
}

function multiply(a, b) {
  return a * b;
}

function divide(a, b) {
  if (b === 0) throw new Error("Cannot divide by zero");
  return a / b;
}

module.exports = { add, subtract, multiply, divide };
```

Create `server.js`:
```javascript
const http = require('http');
const { add, subtract, multiply, divide } = require('./index');

const server = http.createServer((req, res) => {
  res.writeHead(200, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify({
    status: 'running',
    message: 'TaskMaster Calculator API',
    version: '1.0.0'
  }));
});

const PORT = process.env.PORT || 3000;

if (require.main === module) {
  server.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
  });
}

module.exports = server;
```

### Step 2: Add Tests

Install Jest:
```bash
npm install --save-dev jest
```

Update `package.json` scripts:
```json
{
  "scripts": {
    "start": "node server.js",
    "test": "jest --coverage",
    "lint": "echo 'Linting passed (placeholder)'"
  }
}
```

Create `index.test.js`:
```javascript
const { add, subtract, multiply, divide } = require('./index');

describe('Calculator Functions', () => {
  describe('add', () => {
    test('adds two positive numbers', () => {
      expect(add(2, 3)).toBe(5);
    });
    test('adds negative numbers', () => {
      expect(add(-1, -1)).toBe(-2);
    });
    test('adds zero', () => {
      expect(add(5, 0)).toBe(5);
    });
  });

  describe('subtract', () => {
    test('subtracts two numbers', () => {
      expect(subtract(5, 3)).toBe(2);
    });
    test('result can be negative', () => {
      expect(subtract(3, 5)).toBe(-2);
    });
  });

  describe('multiply', () => {
    test('multiplies two numbers', () => {
      expect(multiply(4, 3)).toBe(12);
    });
    test('multiply by zero returns zero', () => {
      expect(multiply(5, 0)).toBe(0);
    });
  });

  describe('divide', () => {
    test('divides two numbers', () => {
      expect(divide(10, 2)).toBe(5);
    });
    test('throws error on divide by zero', () => {
      expect(() => divide(10, 0)).toThrow('Cannot divide by zero');
    });
  });
});
```

### Step 3: Initialize Git and Push to GitHub

```bash
git init
echo "node_modules/" > .gitignore
echo "coverage/" >> .gitignore
git add .
git commit -m "Initial commit: Calculator app with tests"
```

Create a new repository on GitHub (github.com/new), then:
```bash
git remote add origin https://github.com/YOUR_USERNAME/taskmaster-demo.git
git branch -M main
git push -u origin main
```

### Step 4: Create the CI/CD Pipeline

Create the GitHub Actions workflow:

```bash
mkdir -p .github/workflows
```

Create `.github/workflows/ci-cd.yml`:
```yaml
name: TaskMaster CI/CD Pipeline

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  # Stage 1: Code Quality
  lint:
    name: 🔍 Code Quality Check
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Run linter
        run: npm run lint

  # Stage 2: Test
  test:
    name: 🧪 Run Tests
    runs-on: ubuntu-latest
    needs: lint
    strategy:
      matrix:
        node-version: [18, 20, 22]
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Node.js ${{ matrix.node-version }}
        uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node-version }}
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Run tests with coverage
        run: npm test

      - name: Upload coverage report
        if: matrix.node-version == 20
        uses: actions/upload-artifact@v4
        with:
          name: coverage-report
          path: coverage/

  # Stage 3: Build
  build:
    name: 🔨 Build Application
    runs-on: ubuntu-latest
    needs: test
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Build (verify app starts)
        run: |
          node -e "const app = require('./index'); console.log('Build verification: add(2,3) =', app.add(2,3))"
          echo "✅ Build successful!"

      - name: Package application
        run: |
          mkdir -p dist
          cp index.js server.js package.json package-lock.json dist/
          tar -czf taskmaster-v${{ github.run_number }}.tar.gz dist/
          echo "📦 Artifact created: taskmaster-v${{ github.run_number }}.tar.gz"

      - name: Upload build artifact
        uses: actions/upload-artifact@v4
        with:
          name: taskmaster-build
          path: taskmaster-v*.tar.gz

  # Stage 4: Deploy (only on main branch push)
  deploy:
    name: 🚀 Deploy to Production
    runs-on: ubuntu-latest
    needs: build
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    environment: production
    steps:
      - name: Download build artifact
        uses: actions/download-artifact@v4
        with:
          name: taskmaster-build

      - name: Simulate deployment
        run: |
          echo "🚀 Deploying TaskMaster v${{ github.run_number }}..."
          echo "📦 Artifact: $(ls taskmaster-v*.tar.gz)"
          echo "🌍 Environment: Production"
          echo "⏰ Deployed at: $(date)"
          echo "✅ Deployment complete!"

      - name: Post-deployment verification
        run: |
          echo "🔍 Running smoke tests..."
          echo "✅ Health check passed"
          echo "✅ API endpoints responding"
          echo "🎉 Deployment verified successfully!"
```

### Step 5: Push and Watch It Run

```bash
git add .
git commit -m "Add CI/CD pipeline with GitHub Actions"
git push origin main
```

Now go to your GitHub repository → **Actions** tab and watch your pipeline execute!

### Step 6: Test the Pipeline with a Pull Request

1. Create a new branch:
```bash
git checkout -b feature/add-power-function
```

2. Add a new function to `index.js`:
```javascript
function power(base, exponent) {
  return Math.pow(base, exponent);
}

module.exports = { add, subtract, multiply, divide, power };
```

3. Add tests in `index.test.js`:
```javascript
describe('power', () => {
  test('calculates power correctly', () => {
    expect(power(2, 3)).toBe(8);
  });
  test('anything to power 0 is 1', () => {
    expect(power(5, 0)).toBe(1);
  });
});
```

4. Push and create a PR:
```bash
git add .
git commit -m "feat: add power function with tests"
git push origin feature/add-power-function
```

5. Go to GitHub and create a Pull Request. Watch the CI pipeline run on your PR!

### Step 7: Intentionally Break the Build

1. Create another branch:
```bash
git checkout main
git checkout -b feature/broken-code
```

2. Add a deliberately broken test:
```javascript
test('this will fail', () => {
  expect(add(2, 2)).toBe(5);  // This is wrong!
});
```

3. Push and create a PR. Watch the pipeline FAIL and show a red ❌.

## ✅ Expected Output

After completing this exercise, you should have:

1. ✅ A GitHub repository with a Node.js application
2. ✅ Automated tests with Jest
3. ✅ A working GitHub Actions CI/CD pipeline with 4 stages
4. ✅ A successful pipeline run on the main branch (green ✓)
5. ✅ A PR with a passing pipeline
6. ✅ A PR with a deliberately failing pipeline (red ✗)
7. ✅ Build artifacts uploaded to GitHub

Your Actions tab should show pipeline runs with stages:
```
🔍 Code Quality Check  →  🧪 Run Tests (3 versions)  →  🔨 Build  →  🚀 Deploy
```

## 🧠 Key Takeaway

You've just built a real CI/CD pipeline from scratch! This is the same fundamental pattern used by companies from startups to Netflix. Every concept from Chapter 01 — triggers, stages, jobs, artifacts, runners, environments — you've now seen in action. The rest of this guide builds on exactly this foundation.
