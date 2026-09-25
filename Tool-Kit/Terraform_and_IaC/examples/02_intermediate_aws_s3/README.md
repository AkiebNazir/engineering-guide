# Intermediate AWS S3
**Goal:** Provisions a secure AWS S3 bucket with all public access explicitly blocked.
**Key Concepts:** [Providers](../Terraform_and_IaC.md#providers), [Resources](../Terraform_and_IaC.md#resources)
**Prerequisites:** Terraform installed, AWS CLI configured with active credentials.
**Step-by-Step Execution:**
1. `terraform init` (Downloads the AWS provider)
2. `terraform plan` (Shows what resources will be created on AWS)
3. `terraform apply` (Review the plan and type `yes` to provision)
**Try it yourself:** Try adding a new tag to the bucket or configuring S3 bucket versioning by adding a new resource block.
**Teardown:** Run `terraform destroy` and type `yes` to delete the S3 bucket.
