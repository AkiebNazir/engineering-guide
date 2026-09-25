# Advanced Remote State
**Goal:** Illustrates the structure for setting up a Terraform project that uses remote state.
**Key Concepts:** [Remote State and State Locking](../Terraform_and_IaC.md#remote-state-and-state-locking)
**Prerequisites:** Terraform installed, AWS CLI configured.
**Step-by-Step Execution:**
1. Review the configuration to see a basic SNS topic provisioned.
2. `terraform init` 
3. `terraform apply`
**Try it yourself:** Create an S3 bucket manually in the AWS console, then configure a `backend "s3"` block in a `terraform {}` block to migrate your local state to the cloud!
**Teardown:** Run `terraform destroy` to clean up the SNS topic.
