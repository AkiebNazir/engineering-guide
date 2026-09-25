<Chapter 09: Infrastructure as Code>
<Exercise 3: Terraform Modules 🟡>
## 🎯 Objective
Abstract infrastructure components into a reusable Terraform module representing a web server deployment (VPC + Instance mock).

## 📋 Prerequisites
- Understanding of Terraform variables and resources
- Terraform CLI installed

## 📝 Instructions
Modules are self-contained packages of Terraform configurations. We will simulate an AWS module using local resources to understand the structure.

1. Create a directory structure for a module: `modules/web_server/`.
2. Inside the module, create `main.tf`, `variables.tf`, and `outputs.tf`.
   - The module should accept an `environment` variable (e.g., "dev", "prod").
   - The module should create two local files: `vpc_${var.environment}.json` and `instance_${var.environment}.json` to simulate provisioning.
   - The module should output the "instance ID" (just the filename).
3. In your root directory, create a root `main.tf` that calls the `web_server` module twice: once for `dev` and once for `prod`.
4. Run the Terraform workflow to verify it works.

## 💡 Hints
- Call a module using `module "name" { source = "./path/to/module" ... }`.
- When you add or change modules, you must re-run `terraform init`.

## ✅ Expected Output / Solution

**Directory Structure:**
```text
.
├── main.tf
└── modules
    └── web_server
        ├── main.tf
        ├── outputs.tf
        └── variables.tf
```

**1. `modules/web_server/variables.tf`**
```hcl
variable "environment" {
  description = "The environment name (e.g., dev, prod)"
  type        = string
}

variable "instance_type" {
  description = "The size of the instance"
  type        = string
  default     = "t2.micro"
}
```

**2. `modules/web_server/main.tf`**
```hcl
resource "local_file" "vpc" {
  filename = "${path.module}/vpc_${var.environment}.json"
  content  = "{\"vpc_id\": \"vpc-mock-${var.environment}\", \"cidr\": \"10.0.0.0/16\"}"
}

resource "local_file" "instance" {
  filename = "${path.module}/instance_${var.environment}.json"
  content  = "{\"instance_id\": \"i-mock-${var.environment}\", \"type\": \"${var.instance_type}\"}"
  
  # Ensure VPC is created before the instance
  depends_on = [local_file.vpc]
}
```

**3. `modules/web_server/outputs.tf`**
```hcl
output "instance_file_path" {
  value = local_file.instance.filename
}
```

**4. Root `main.tf`**
```hcl
module "dev_web" {
  source        = "./modules/web_server"
  environment   = "dev"
  instance_type = "t2.micro"
}

module "prod_web" {
  source        = "./modules/web_server"
  environment   = "prod"
  instance_type = "t3.large"
}

output "dev_instance" {
  value = module.dev_web.instance_file_path
}

output "prod_instance" {
  value = module.prod_web.instance_file_path
}
```

**Execution**
```bash
terraform init   # Important to initialize the modules!
terraform apply -auto-approve
```

## 🧠 Key Takeaway
Modules are the primary way to organize and reuse code in Terraform. Instead of copying and pasting resource blocks for every environment or application, you define a module once and instantiate it multiple times with different variables.
