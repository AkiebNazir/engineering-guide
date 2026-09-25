# Exercise 04: Compare CI/CD Tools Research 🟡

## 🎯 Objective

Research and compare popular CI/CD tools to understand the landscape and make informed choices for different project scenarios.

## 📋 Prerequisites
- Understanding of CI/CD concepts from Chapter 01
- Web browser for research

## 📝 Instructions

### Task 1: Research 5 CI/CD Tools

Research the following CI/CD tools and fill in the comparison table:

1. **GitHub Actions**
2. **GitLab CI/CD**
3. **Jenkins**
4. **CircleCI**
5. **Azure DevOps Pipelines**

For each tool, find:

| Criteria | GitHub Actions | GitLab CI | Jenkins | CircleCI | Azure DevOps |
|----------|---------------|-----------|---------|----------|-------------|
| Open Source? | | | | | |
| Cloud or Self-Hosted? | | | | | |
| Config File Format | | | | | |
| Free Tier Limits | | | | | |
| Best For | | | | | |
| Learning Curve | | | | | |
| Marketplace/Plugins | | | | | |

### Task 2: Scenario-Based Recommendations

For each scenario below, recommend the BEST CI/CD tool and explain WHY:

1. **Startup with 3 developers**, code on GitHub, need something free and quick to set up
2. **Enterprise bank** with strict security requirements, everything must be on-premises
3. **Open-source project** with 100+ contributors from around the world
4. **Company already using Azure cloud** for all infrastructure
5. **Team wanting everything in one platform** (code, CI/CD, container registry, issue tracking)

### Task 3: Read a Real Config File

Go to GitHub and find a real `.github/workflows/*.yml` file from any popular project. Copy it and annotate every line with a comment explaining what it does.

Example:
```yaml
name: CI  # Name of the workflow displayed in GitHub UI
on: [push]  # Trigger: runs when code is pushed
jobs:       # Collection of all jobs in this workflow
  test:     # Job name: "test"
    runs-on: ubuntu-latest  # Use Ubuntu as the runner OS
    # ... annotate every line
```

## ✅ Expected Output / Solution

### Task 1 Answer:

| Criteria | GitHub Actions | GitLab CI | Jenkins | CircleCI | Azure DevOps |
|----------|---------------|-----------|---------|----------|-------------|
| Open Source? | No (platform) | Core is open | Yes | No | No |
| Cloud or Self-Hosted? | Both | Both | Self-hosted (mainly) | Cloud (mainly) | Both |
| Config File Format | YAML | YAML | Groovy (Jenkinsfile) | YAML | YAML |
| Free Tier | 2000 min/month | 400 min/month | Free (self-hosted) | 6000 min/month | 1800 min/month |
| Best For | GitHub-hosted projects | All-in-one DevOps | Complex enterprise | Fast builds | Microsoft ecosystem |
| Learning Curve | Low | Low-Medium | High | Low | Medium |
| Marketplace | 20,000+ actions | Templates | 1800+ plugins | Orbs | Extensions |

### Task 2 Answers:

1. **Startup → GitHub Actions** — Free for public repos, already on GitHub, minimal setup, huge marketplace
2. **Enterprise bank → Jenkins** — Fully self-hosted, complete control over security, extensive plugin ecosystem
3. **Open-source project → GitHub Actions** — Free for public repos, contributors already have GitHub accounts, easy to configure
4. **Azure company → Azure DevOps** — Native integration with Azure services, unified billing, seamless deployment to Azure
5. **All-in-one platform → GitLab CI** — GitLab provides code hosting, CI/CD, container registry, issue tracking, and more in a single platform

## 🧠 Key Takeaway

There's no single "best" CI/CD tool — the right choice depends on your team size, existing infrastructure, security requirements, and budget. Understanding the landscape helps you make informed decisions.
