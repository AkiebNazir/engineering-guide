<Chapter 09: Infrastructure as Code>
<Exercise 4: Automating Terraform with CI/CD 🟡>
## 🎯 Objective
Write a GitHub Actions CI/CD pipeline that safely executes Terraform operations: `plan` on Pull Requests, and `apply` on merges to the `main` branch.

## 📋 Prerequisites
- Understanding of GitHub Actions syntax
- Understanding of the Terraform workflow

## 📝 Instructions
1. Create a YAML workflow file (e.g., `.github/workflows/terraform.yml`).
2. Configure it to trigger on `push` to `main` and on `pull_request`.
3. Set up a job with the following steps:
   - Checkout the code.
   - Setup Terraform (using `hashicorp/setup-terraform`).
   - Format check (`terraform fmt -check`).
   - Initialize (`terraform init`).
   - Validate (`terraform validate`).
   - Plan (`terraform plan`) — ONLY if it's a Pull Request.
   - Apply (`terraform apply -auto-approve`) — ONLY if it's a push to `main`.
4. Mock the AWS credentials via environment variables so the pipeline knows how to authenticate.

## 💡 Hints
- Use `if: github.event_name == 'pull_request'` to conditionally run the plan step.
- Use `if: github.ref == 'refs/heads/main' && github.event_name == 'push'` to conditionally run the apply step.

## ✅ Expected Output / Solution

**`.github/workflows/terraform.yml`**

```yaml
name: "Terraform CI/CD"

on:
  push:
    branches:
      - main
  pull_request:

jobs:
  terraform:
    name: "Terraform Execution"
    runs-on: ubuntu-latest
    
    # Environment variables for AWS Authentication (Mocked)
    env:
      AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
      AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
      AWS_REGION: "us-east-1"

    steps:
      - name: Checkout Code
        uses: actions/checkout@v3

      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v2
        with:
          terraform_version: 1.5.0

      - name: Terraform Format Check
        id: fmt
        run: terraform fmt -check -diff
        continue-on-error: true

      - name: Terraform Init
        id: init
        run: terraform init

      - name: Terraform Validate
        id: validate
        run: terraform validate -no-color

      - name: Terraform Plan
        id: plan
        if: github.event_name == 'pull_request'
        run: terraform plan -no-color
        continue-on-error: true

      # Optional: Post Plan to PR as a comment (Advanced but common)
      - name: Comment PR with Plan
        uses: actions/github-script@v6
        if: github.event_name == 'pull_request'
        env:
          PLAN: "terraform\n${{ steps.plan.outputs.stdout }}"
        with:
          script: |
            const output = `#### Terraform Format and Style 🖌\`${{ steps.fmt.outcome }}\`
            #### Terraform Initialization ⚙️\`${{ steps.init.outcome }}\`
            #### Terraform Plan 📖\`${{ steps.plan.outcome }}\`
            
            <details><summary>Show Plan</summary>
            
            \`\`\`\n
            ${process.env.PLAN}
            \`\`\`
            
            </details>`;
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: output
            })

      - name: Terraform Apply
        if: github.ref == 'refs/heads/main' && github.event_name == 'push'
        run: terraform apply -auto-approve -input=false
```

## 🧠 Key Takeaway
Executing IaC in a pipeline rather than locally removes the "it works on my machine" problem. By performing `terraform plan` on PRs, team members can review the exact infrastructure changes before merging. Upon merge, the `apply` operation automatically synchronizes the real world with the source code repository.
