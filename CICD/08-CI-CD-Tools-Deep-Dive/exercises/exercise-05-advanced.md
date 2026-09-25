# Exercise 5: Reusable Workflows in GitHub Actions 🔴

## 🎯 Objective
Create an enterprise-grade CI/CD system by abstracting build logic into a Reusable Workflow, and then call that workflow from a primary pipeline.

## 📋 Prerequisites
- Completion of Exercises 1 and 3.
- Understanding of standardizing CI pipelines across multiple repositories.

## 📝 Instructions

1. **The Scenario**
   Your enterprise has 50 microservices. Instead of copying and pasting the exact same Go build steps into 50 different `.github/workflows/ci.yml` files, you want to create a single central standard workflow and have every microservice call it.

2. **Create the Reusable Workflow (The "Template")**
   Create a file at `.github/workflows/reusable-go.yml`. This workflow will NOT trigger on pushes; it triggers on `workflow_call`.

   ```yaml
   # .github/workflows/reusable-go.yml
   name: Shared Go Pipeline

   on:
     workflow_call:
       inputs:
         go-version:
           required: true
           type: string
           description: "Version of Go to use"
       secrets:
         org_token:
           required: true
           description: "Token for downloading private enterprise modules"

   jobs:
     build-and-test:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v4
         
         - name: Set up Go ${{ inputs.go-version }}
           uses: actions/setup-go@v5
           with:
             go-version: ${{ inputs.go-version }}

         # Using the secret passed from the caller
         - name: Authenticate with private repo
           run: git config --global url."https://${{ secrets.org_token }}@github.com/my-org/".insteadOf "https://github.com/my-org/"

         - name: Build
           run: go build -v ./...

         - name: Test
           run: go test -v ./...
   ```

3. **Create the Caller Workflow (The "Microservice")**
   Now, act as the developer of "Microservice A". You want to use the enterprise template.
   Create `.github/workflows/microservice-ci.yml`.

   ```yaml
   # .github/workflows/microservice-ci.yml
   name: Microservice A CI

   on:
     push:
       branches: [ "main" ]

   jobs:
     # Call the reusable workflow
     call-shared-go-pipeline:
       # Syntax: {owner}/{repo}/.github/workflows/{filename}@{ref}
       # Since we are in the same repo for this exercise, we use local path:
       uses: ./.github/workflows/reusable-go.yml
       with:
         go-version: '1.21'
       secrets:
         org_token: ${{ secrets.GITHUB_TOKEN }}
   ```

## 💡 Hints
- `workflow_call` makes a workflow reusable. It acts almost like a function definition in programming, specifying `inputs` and `secrets` it expects as arguments.
- `uses:` in a job block (not a step block) calls a reusable workflow. 
- In the real world, the reusable workflow would live in a centralized repository like `my-enterprise/ci-templates/.github/workflows/go.yml@main`.

## ✅ Expected Output / Solution
When you push code to `main`, GitHub Actions will trigger `Microservice A CI`. In the UI, the job will expand to show the steps defined in `reusable-go.yml`. The pipeline successfully configures Go 1.21 (passed as an input) and authenticates using the `org_token` secret.

## 🧠 Key Takeaway
Reusable Workflows allow you to practice DRY (Don't Repeat Yourself) principles in CI/CD. By maintaining a centralized repository of approved CI workflows, DevOps teams can enforce security and build standards across hundreds of repositories effortlessly.
