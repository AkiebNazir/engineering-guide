# Basic Local File
**Goal:** Demonstrates the simplest Terraform configuration by creating a local file on your machine.
**Key Concepts:** [Providers](../Terraform_and_IaC.md#providers), [Resources](../Terraform_and_IaC.md#resources)
**Prerequisites:** Terraform installed.
**Step-by-Step Execution:**
1. `terraform init` (Initializes the local provider)
2. `terraform plan` (Shows it will create `hello.txt`)
3. `terraform apply -auto-approve` (Creates the file)
4. `cat hello.txt` (Verify the file contents)
**Try it yourself:** Change the `filename` or `content` in `main.tf` and run `terraform apply` again to see how Terraform updates the resource.
**Teardown:** Run `terraform destroy -auto-approve` to clean up.
