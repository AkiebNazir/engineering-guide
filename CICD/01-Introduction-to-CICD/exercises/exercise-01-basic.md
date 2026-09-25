# Exercise 01: Identify CI/CD in the Wild 🟢

## 🎯 Objective

Learn to recognize CI/CD concepts by analyzing a real-world open-source project's pipeline configuration.

## 📋 Prerequisites
- A web browser
- A GitHub account (free)

## 📝 Instructions

### Step 1: Visit a Real Open-Source Project

Go to the following GitHub repository:  
👉 **https://github.com/facebook/react**

### Step 2: Find the CI/CD Configuration

1. Navigate to the `.github/workflows/` directory (or look for `.circleci/`, `.travis.yml`, `Jenkinsfile`)
2. Open one of the workflow YAML files

### Step 3: Answer These Questions

Write your answers in a text file or notebook:

1. **What CI/CD tool does this project use?** (GitHub Actions, CircleCI, Jenkins, etc.)
2. **What events trigger the pipeline?** (push, pull_request, schedule, etc.)
3. **How many stages/jobs does the pipeline have?** List them.
4. **What types of tests does the pipeline run?** (unit, integration, lint, etc.)
5. **Does this project use Continuous Delivery or Continuous Deployment?** How can you tell?

### Step 4: Repeat with Another Project

Choose ONE more project and answer the same questions:
- **https://github.com/nodejs/node**
- **https://github.com/kubernetes/kubernetes**
- **https://github.com/microsoft/vscode**

## 💡 Hints

- Look in the root directory for files like `.github/workflows/*.yml`, `Jenkinsfile`, `.circleci/config.yml`
- The `on:` section in GitHub Actions tells you the triggers
- Jobs are listed under the `jobs:` section

## ✅ Expected Output

A document with answers for 2 projects. Example format:

```
Project: facebook/react
CI/CD Tool: [Your Answer]
Triggers: [Your Answer]
Stages/Jobs: [Your Answer]
Test Types: [Your Answer]
Delivery vs Deployment: [Your Answer]
```

## 🧠 Key Takeaway

CI/CD is not just theory — it's actively used by every major software project in the world. Learning to read pipeline configurations is a foundational skill.
