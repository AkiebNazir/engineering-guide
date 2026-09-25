<Chapter 09: Infrastructure as Code>
<Exercise 2: Variables and Outputs 🟢>
## 🎯 Objective
Learn how to make Terraform configurations dynamic and reusable using input variables, and how to extract data using outputs.

## 📋 Prerequisites
- Completion of Exercise 1
- Terraform CLI installed

## 📝 Instructions
1. Create a `variables.tf` file to define input variables: `file_name` (default: "config.txt") and `file_content` (type: string, no default).
2. Create a `main.tf` file that uses the `local_file` resource, injecting the variables instead of hardcoding values.
3. Create an `outputs.tf` file to expose the absolute path of the generated file and its file permission mode.
4. Create a `terraform.tfvars` file to supply the value for `file_content`.
5. Run the Terraform workflow to apply the changes.

## 💡 Hints
- Variables are referenced using `var.variable_name`.
- Outputs are defined using the `output "name" { value = ... }` block.
- A `.tfvars` file is automatically loaded by Terraform to populate variable values if it's named exactly `terraform.tfvars` or `*.auto.tfvars`.

## ✅ Expected Output / Solution

**1. `variables.tf`**
```hcl
variable "file_name" {
  description = "The name of the file to create"
  type        = string
  default     = "config.txt"
}

variable "file_content" {
  description = "The content to place inside the file"
  type        = string
}
```

**2. `main.tf`**
```hcl
terraform {
  required_providers {
    local = {
      source  = "hashicorp/local"
      version = "~> 2.4.0"
    }
  }
}

resource "local_file" "dynamic_file" {
  filename = "${path.module}/${var.file_name}"
  content  = var.file_content
}
```

**3. `outputs.tf`**
```hcl
output "absolute_file_path" {
  description = "The absolute path of the generated file"
  value       = local_file.dynamic_file.filename
}

output "file_permissions" {
  description = "The permissions of the generated file"
  value       = local_file.dynamic_file.file_permission
}
```

**4. `terraform.tfvars`**
```hcl
file_content = "database_url=postgres://user:pass@localhost:5432/db\napi_key=super_secret_key"
```

**Execution Steps**
```bash
terraform init
terraform plan
terraform apply -auto-approve
```

*Output snippet:*
```text
Apply complete! Resources: 1 added, 0 changed, 0 destroyed.

Outputs:

absolute_file_path = "./config.txt"
file_permissions = "0777"
```

## 🧠 Key Takeaway
Variables (`variables.tf`) allow you to parameterize your IaC, making it flexible for different environments (Dev, Staging, Prod). Outputs (`outputs.tf`) provide a way to extract computed information (like IP addresses, IDs, or paths) from your resources to pass into other tools or display to the user.
