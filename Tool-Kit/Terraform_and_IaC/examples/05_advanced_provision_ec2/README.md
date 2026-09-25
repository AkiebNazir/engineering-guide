# Advanced Provision EC2
**Goal:** Provisions a complete EC2 web server running Nginx, utilizing a dynamic data source to fetch the latest Ubuntu AMI and user data for bootstrapping.
**Key Concepts:** [Data Sources](../Terraform_and_IaC.md#data-sources), [AWS VPC and EC2 Instance](../Terraform_and_IaC.md#aws-vpc-and-ec2-instance)
**Prerequisites:** Terraform installed, AWS CLI configured.
**Step-by-Step Execution:**
1. `terraform init`
2. `terraform apply` (Type `yes` to provision the security group and instance)
3. The output will print `public_ip`. Wait a minute for the instance to boot, then open `http://<public_ip>` in your browser to see "Deployed via Terraform!".
**Try it yourself:** Change the instance type from `t2.micro` to `t3.micro`, or modify the `user_data` script to install Apache instead of Nginx.
**Teardown:** Run `terraform destroy` and type `yes` to terminate the instance and delete the security group.
