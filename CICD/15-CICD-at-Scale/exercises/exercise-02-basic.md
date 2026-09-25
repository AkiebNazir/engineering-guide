# Exercise 2: Pipeline Templates (Go) 🟢

## 🎯 Objective
Create a centralized "Golden Path" pipeline template for Go microservices, enforcing code quality and vulnerability scanning.

## 📋 Prerequisites
- Basic understanding of CI/CD YAML.
- Go installed.

## 📝 Instructions

1. In your central platform repository, create `central-platform/templates/go-ci.yml`.

2. Write the template definition:
   ```yaml
   name: Go Golden Path
   
   on:
     workflow_call:
       inputs:
         go-version:
           required: true
           type: string
       secrets:
         PRIVATE_MOD_TOKEN:
           required: false
   
   jobs:
     verify:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v4
         
         - name: Setup Go
           uses: actions/setup-go@v5
           with:
             go-version: ${{ inputs.go-version }}
             cache: true
             
         - name: Configure Private Modules
           if: ${{ env.PRIVATE_MOD_TOKEN != '' }}
           run: git config --global url."https://${{ secrets.PRIVATE_MOD_TOKEN }}@github.com".insteadOf "https://github.com"
             
         - name: Go Format Check
           run: |
             if [ -n "$(gofmt -l .)" ]; then
               echo "Code is not formatted. Run gofmt."
               exit 1
             fi
             
         - name: Go Vet
           run: go vet ./...
           
         - name: Govulncheck
           run: |
             go install golang.org/x/vuln/cmd/govulncheck@latest
             govulncheck ./...
             
         - name: Tests
           run: go test -v -race -cover ./...
   ```

3. In a consumer repository, implement the template:
   ```yaml
   name: Backend CI
   
   on: [pull_request]
   
   jobs:
     ci:
       uses: my-org/central-platform/.github/workflows/go-ci.yml@v1
       with:
         go-version: "1.21"
       secrets:
         PRIVATE_MOD_TOKEN: ${{ secrets.GITHUB_TOKEN }}
   ```

## 💡 Hints
- The `secrets` block in `workflow_call` allows the calling workflow to pass sensitive credentials (like tokens for private Go modules) to the reusable workflow safely.

## ✅ Expected Output / Solution
A standardized pipeline that enforces formatting, static analysis (`go vet`), vulnerability scanning (`govulncheck`), and testing. 

## 🧠 Key Takeaway
By baking `govulncheck` and standard Go tools into the central template, the Platform Team ensures that no Go service reaches production with known vulnerabilities or unformatted code, without requiring developers to write boilerplate CI code.
