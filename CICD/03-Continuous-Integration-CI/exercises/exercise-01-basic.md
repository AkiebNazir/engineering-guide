# Exercise 01: Read and Understand a CI Config 🟢

## 🎯 Objective
Read a GitHub Actions workflow file and explain every line in plain English.

## 📋 Prerequisites
- Chapter 03 theory completed

## 📝 Instructions

### The Config File

Read this GitHub Actions workflow carefully and answer the questions below:

```yaml
name: Node.js CI

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        node-version: [18, 20]
    steps:
    - uses: actions/checkout@v4
    - name: Use Node.js ${{ matrix.node-version }}
      uses: actions/setup-node@v4
      with:
        node-version: ${{ matrix.node-version }}
        cache: 'npm'
    - run: npm ci
    - run: npm run build --if-present
    - run: npm test
```

### Questions

1. **What is the name of this workflow?**
2. **When does this pipeline run?** (list all triggers)
3. **What operating system does this run on?**
4. **How many total jobs will be created?** (hint: look at the matrix)
5. **What does `actions/checkout@v4` do?**
6. **What's the difference between `npm ci` and `npm install`?**
7. **What does `cache: 'npm'` do?**
8. **What does `--if-present` mean in `npm run build --if-present`?**
9. **If Node 18 tests pass but Node 20 tests fail, does the build pass or fail?**
10. **Draw the execution flow as a diagram.**

## ✅ Expected Output

1. "Node.js CI"
2. Push to main branch AND Pull Requests targeting main
3. Ubuntu (latest version)
4. **2 jobs** — one for Node 18, one for Node 20 (matrix creates 2 configurations)
5. Clones the repository code onto the runner
6. `npm ci` is faster and uses exact versions from `package-lock.json`; `npm install` might update versions
7. Caches the npm dependency folder to speed up future builds
8. Only runs `build` if that script exists in package.json; won't fail if missing
9. **Fail** — all matrix combinations must pass by default
10. Diagram should show: Push → Job1 (Node 18) + Job2 (Node 20) in parallel → both must pass

## 🧠 Key Takeaway
Being able to read and understand CI configurations is as important as writing them. Every line has a purpose.
