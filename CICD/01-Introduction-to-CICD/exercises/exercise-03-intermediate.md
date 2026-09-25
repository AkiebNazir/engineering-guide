# Exercise 03: Design a Pipeline on Paper 🟡

## 🎯 Objective

Design a CI/CD pipeline for a hypothetical web application, thinking through each stage, its purpose, and what happens when things fail.

## 📋 Prerequisites
- Understanding of CI/CD concepts from Chapter 01
- Basic understanding of web applications

## 📝 Instructions

### Scenario

You are the lead developer of **"TaskMaster"** — a web-based task management application. The tech stack is:
- **Frontend:** React (JavaScript)
- **Backend:** Node.js with Express
- **Database:** PostgreSQL
- **Hosting:** AWS (Amazon Web Services)

Your team has 5 developers who all push code daily.

### Task 1: Design Your Pipeline Stages

Create a diagram (on paper, whiteboard, or use a tool like draw.io) showing your pipeline with:

1. **At least 5 stages** — name each one and describe what happens in it
2. **Triggers** — what event(s) start the pipeline?
3. **Failure handling** — what happens if each stage fails?
4. **Environments** — list all the environments code passes through

### Task 2: Answer These Design Questions

1. **Should the frontend and backend have separate pipelines or one combined pipeline?** Justify your answer.
2. **How long should your pipeline take to complete?** Why?
3. **What happens if a developer pushes code that breaks the build?** Write out the exact process.
4. **Should you use Continuous Delivery or Continuous Deployment?** Why? Consider that this app handles user data.
5. **What metrics would you track to know your pipeline is healthy?**

### Task 3: Write a Pipeline Specification

Create a YAML-like specification (it doesn't need to be valid YAML — just structured):

```
Pipeline: TaskMaster CI/CD
Trigger: [your answer]

Stage 1: [name]
  Steps:
    - [step 1]
    - [step 2]
  On Failure: [what happens]

Stage 2: [name]
  ...
```

## 💡 Hints

- Think about what could go wrong at each stage
- Consider: lint → build → unit test → integration test → security scan → deploy staging → deploy production
- Think about what runs in parallel vs. sequentially

## ✅ Expected Output / Solution

### Sample Pipeline Design:

```
Pipeline: TaskMaster CI/CD
Trigger: Push to main branch, Pull Request to main

Stage 1: Code Quality
  Steps:
    - Run ESLint on frontend code
    - Run ESLint on backend code
    - Check code formatting with Prettier
  On Failure: Block merge, notify developer via Slack
  Duration: ~1 minute

Stage 2: Build
  Steps:
    - Install npm dependencies (frontend)
    - Install npm dependencies (backend)
    - Build React production bundle
    - Compile TypeScript (if used)
  On Failure: Notify developer, block pipeline
  Duration: ~2 minutes

Stage 3: Unit Tests
  Steps:
    - Run Jest tests for frontend (React components)
    - Run Jest tests for backend (API routes, services)
    - Generate code coverage report
    - Fail if coverage < 80%
  On Failure: Block pipeline, post coverage report to PR
  Duration: ~3 minutes

Stage 4: Integration Tests
  Steps:
    - Spin up PostgreSQL test database
    - Run API integration tests
    - Run frontend E2E tests with Cypress
  On Failure: Block pipeline, save test screenshots
  Duration: ~5 minutes

Stage 5: Security Scan
  Steps:
    - Run npm audit for vulnerable dependencies
    - Run SAST (Static Application Security Testing)
    - Check for secrets in code
  On Failure: Block pipeline, alert security team
  Duration: ~2 minutes

Stage 6: Deploy to Staging
  Steps:
    - Build Docker images
    - Push to container registry
    - Deploy to staging environment
    - Run smoke tests
  On Failure: Rollback staging, notify team
  Duration: ~3 minutes

Stage 7: Deploy to Production (Manual Approval)
  Steps:
    - Wait for manual approval from team lead
    - Blue/green deployment to production
    - Run production smoke tests
    - Monitor error rates for 15 minutes
  On Failure: Automatic rollback, page on-call engineer
  Duration: ~5 minutes + approval wait

Total Pipeline Duration: ~20 minutes (excluding approval wait)
```

### Design Questions Answers:

1. **Separate or combined?** Use a **monorepo with separate pipelines** that share a common deploy stage. This way, a frontend-only change doesn't trigger backend tests.

2. **Pipeline duration:** **Under 15 minutes** for the CI part. Developers need fast feedback. If it takes too long, they'll context-switch and lose focus.

3. **Broken build process:** Developer is notified immediately → they must drop everything and fix it → no other PRs are merged until the build is green → this ensures the main branch is always deployable.

4. **Delivery vs Deployment:** **Continuous Delivery** (with manual approval for production) because the app handles user data. You want a human to verify before pushing to production, especially for database migrations.

5. **Pipeline health metrics:**
   - Build success rate (target: >95%)
   - Average pipeline duration
   - Mean time to recovery (MTTR) when builds break
   - Test flakiness rate
   - Deployment frequency

## 🧠 Key Takeaway

Designing a pipeline requires thinking about speed, safety, and failure handling. A good pipeline is fast enough to keep developers productive and reliable enough to catch problems before they reach users.
