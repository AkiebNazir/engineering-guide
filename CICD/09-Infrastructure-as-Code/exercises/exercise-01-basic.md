<Chapter 09: Infrastructure as Code>
<Exercise 1: Basic Terraform Setup 🟢>
## 🎯 Objective
Understand the foundational Terraform workflow (init, plan, apply) by defining a simple local file resource.

## 📋 Prerequisites
- Terraform CLI installed (version 1.0+)
- Basic terminal knowledge

## 📝 Instructions
1. Create a new directory for this exercise and navigate into it.
2. Create a configuration file named `main.tf`.
3. Configure the `local` provider in the `terraform` block.
4. Define a `local_file` resource named `greeting` that will create a file at `./hello.txt` with the content `"Hello, Infrastructure as Code!"`.
5. Run the command to initialize the working directory.
6. Run the command to generate and review an execution plan.
7. Apply the changes to create the file.
8. Verify that `hello.txt` was created successfully.

## 💡 Hints
- The `terraform` block defines required providers. For local files, use `hashicorp/local`.
- The resource syntax is `resource "provider_type" "name" { ... }`.
- The core workflow commands are `terraform init`, `terraform plan`, and `terraform apply`.

## ✅ Expected Output / Solution

**Step 1: Create `main.tf`**

```hcl
terraform {
  required_providers {
    local = {
      source  = "hashicorp/local"
      version = "~> 2.4.0"
    }
  }
}

provider "local" {}

resource "local_file" "greeting" {
  filename = "${path.module}/hello.txt"
  content  = "Hello, Infrastructure as Code!"
}
```

**Step 2: Initialize Terraform**
Run this in your terminal to download the `local` provider plugin:
```bash
terraform init
```

**Step 3: Plan the Execution**
Review what Terraform intends to do:
```bash
terraform plan
```
*Output snippet:*
```text
Terraform will perform the following actions:
  # local_file.greeting will be created
  + resource "local_file" "greeting" {
      + content              = "Hello, Infrastructure as Code!"
      + filename             = "./hello.txt"
      ...
    }
```

**Step 4: Apply the Changes**
Execute the plan and type `yes` when prompted:
```bash
terraform apply
```

**Step 5: Verify**
```bash
cat hello.txt
# Output: Hello, Infrastructure as Code!
```

## 🧠 Key Takeaway
Terraform’s declarative nature allows you to define *what* you want (a file with specific content), while the engine handles *how* to create it. The `init` -> `plan` -> `apply` cycle is the universal workflow for all Terraform deployments, ensuring predictability and safety.
