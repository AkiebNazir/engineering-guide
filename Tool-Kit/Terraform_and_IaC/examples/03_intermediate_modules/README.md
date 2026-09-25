# Intermediate Modules
**Goal:** Demonstrates how to use local Terraform modules to promote reusability and DRY code by creating multiple secure S3 buckets using a single module template.
**Key Concepts:** [Modules](../Terraform_and_IaC.md#modules)
**Prerequisites:** Terraform installed, AWS CLI configured.
**Step-by-Step Execution:**
1. `terraform init` (Initializes the directory and loads the local module)
2. `terraform plan` (Shows it will create two sets of resources from the module)
3. `terraform apply` (Review and type `yes`)
**Try it yourself:** Add a third `module` block in `main.tf` to create a bucket for "database_backups".
**Teardown:** Run `terraform destroy` and type `yes` to delete all resources.
