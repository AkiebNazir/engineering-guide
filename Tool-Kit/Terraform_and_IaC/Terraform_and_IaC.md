# Terraform & Infrastructure as Code

## Introduction to IaC
Infrastructure as Code (IaC) is the process of managing and provisioning computing infrastructure through machine-readable definition files, rather than physical hardware configuration or interactive configuration tools.

### Benefits of IaC
- **Consistency**: Environments are built exactly the same way every time.
- **Speed**: Automates manual processes, speeding up deployments.
- **Version Control**: Infrastructure definitions can be versioned, reviewed, and audited.
- **Reusability**: Code can be modularized and reused across different projects or environments.

## Interactive Examples
We provide several practical examples in the `examples/` directory to help you learn Terraform step-by-step:
- [Basic Local File](examples/01_basic_local_file)
- [Intermediate AWS S3](examples/02_intermediate_aws_s3)
- [Intermediate Modules](examples/03_intermediate_modules)
- [Advanced Remote State](examples/04_advanced_remote_state)
- [Advanced Provision EC2](examples/05_advanced_provision_ec2)

## Introduction to Terraform
Terraform by HashiCorp is an open-source IaC tool that allows you to define both cloud and on-prem resources in human-readable configuration files that you can version, reuse, and share.

### Key Concepts in Terraform

#### HCL Syntax
HashiCorp Configuration Language (HCL) is designed to be human-readable and machine-friendly.

#### Providers
Providers are plugins that implement resource types. A provider handles the API interactions with a service (e.g., AWS, Azure, GCP).

#### Resources
Resources are the most important element in the Terraform language. Each resource block describes one or more infrastructure objects, such as compute instances, virtual networks, or higher-level components such as DNS records.

#### Data Sources
Data sources allow data to be fetched or computed for use elsewhere in Terraform configuration. Use them to read information defined outside of Terraform.

#### Modules
> [!TIP]
> See the [Intermediate Modules example](examples/03_intermediate_modules) for a hands-on demonstration of building and using reusable Terraform modules.

Modules are containers for multiple resources that are used together. A module consists of a collection of `.tf` files kept together in a directory.

## State Management (`.tfstate`)
Terraform must store state about your managed infrastructure and configuration. This state is used by Terraform to map real-world resources to your configuration, keep track of metadata, and improve performance for large infrastructures.

### Remote State and State Locking
> [!TIP]
> Check out the [Advanced Remote State example](examples/04_advanced_remote_state) to see how to configure an S3 backend and DynamoDB table for locking in practice.

In a team environment, local state files are problematic. 
- **Remote State**: Store state in a remote data store (like AWS S3, Google Cloud Storage, or Terraform Cloud).
- **State Locking**: Prevents concurrent executions from corrupting the state file. In AWS, this is typically done using an S3 bucket for the state and a DynamoDB table for locking.

```arch
node terraform "Terraform CLI" at 1,0 icon=terraform-icon
node s3 "S3" at 0,1 icon=aws-s3 sub="State File"
node dynamodb "DynamoDB" at 1,1 icon=aws-dynamodb sub="Locking"
node aws "AWS API" at 2,1 icon=aws-api-gateway
terraform -> s3
terraform -> dynamodb
terraform -> aws
```

## Terraform Workflow
- `terraform init`: Initializes a working directory containing Terraform configuration files. Downloads providers and modules.
- `terraform plan`: Creates an execution plan. It shows what actions Terraform will take to change the infrastructure to match the configuration.
- `terraform apply`: Executes the actions proposed in a Terraform plan.
- `terraform destroy`: Destroys all remote objects managed by a particular Terraform configuration.
- `terraform import`: Imports existing infrastructure into Terraform state.

## Production-Ready Example

### S3 Backend Configuration
```hcl
terraform {
  backend "s3" {
    bucket         = "my-terraform-state-bucket"
    key            = "global/s3/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform-locks"
    encrypt        = true
  }
}
```

### AWS VPC and EC2 Instance
> [!TIP]
> Practice provisioning EC2 instances with the [Advanced Provision EC2 example](examples/05_advanced_provision_ec2).

```hcl
provider "aws" {
  region = "us-east-1"
}

resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
  
  tags = {
    Name = "main-vpc"
  }
}

resource "aws_subnet" "subnet1" {
  vpc_id     = aws_vpc.main.id
  cidr_block = "10.0.1.0/24"
  
  tags = {
    Name = "MainSubnet1"
  }
}

resource "aws_instance" "web" {
  ami           = "ami-0c55b159cbfafe1f0" # Example AMI
  instance_type = "t2.micro"
  subnet_id     = aws_subnet.subnet1.id

  tags = {
    Name = "HelloWorld"
  }
}
```

## MAANG-Level Interview Questions

1. **What is the difference between Terraform and Ansible?**
   *Answer*: Terraform is primarily an orchestration tool designed to provision infrastructure (declarative), whereas Ansible is primarily a configuration management tool designed to configure software on existing infrastructure (procedural/declarative). They are often used together.

2. **Explain the purpose of `terraform state` and why it is critical.**
   *Answer*: The state file (`terraform.tfstate`) maps real-world resources to the configuration, tracks metadata, and improves performance. It is critical because Terraform uses it to determine what changes need to be applied. Without it, Terraform cannot manage existing resources.

3. **How do you handle secrets in Terraform?**
   *Answer*: Never hardcode secrets in `.tf` files. Use environment variables (e.g., `TF_VAR_db_password`), secret management systems (like AWS Secrets Manager or HashiCorp Vault) fetched via data sources, or KMS encryption. State files containing secrets should be encrypted at rest and access-controlled.

4. **What is a Terraform module and why should you use them?**
   *Answer*: A module is a container for multiple resources that are used together. Modules promote reusability, organization, and DRY (Don't Repeat Yourself) principles. They allow teams to create standardized, testable infrastructure components.

5. **Describe the scenario where you would use `terraform import`.**
   *Answer*: If you have existing infrastructure created manually or by another tool, you use `terraform import` to bring it under Terraform's management. It adds the resource to the state file, but you still must write the corresponding HCL configuration.

6. **What is state locking and how is it implemented in AWS?**
   *Answer*: State locking prevents multiple users from modifying the state file simultaneously, which could cause corruption. In AWS, this is typically implemented by using an S3 backend for the state file and a DynamoDB table for the lock mechanism.

7. **How does Terraform handle dependencies between resources?**
   *Answer*: Terraform implicitly handles dependencies through resource interpolation (e.g., `aws_instance.web.subnet_id = aws_subnet.main.id`). It builds a dependency graph to determine the correct order of creation. Explicit dependencies can be defined using the `depends_on` meta-argument.

8. **What are Data Sources in Terraform?**
   *Answer*: Data sources allow Terraform to fetch data from outside its configuration. This could be querying an existing AWS VPC ID, fetching the latest AMI ID, or reading a secret from AWS Secrets Manager.

9. **Explain `terraform plan` and its significance in a CI/CD pipeline.**
   *Answer*: `terraform plan` generates an execution plan showing what Terraform will do without actually making changes. In CI/CD, the plan output can be saved and reviewed (often automated or manually approved) before `terraform apply` is executed, ensuring predictability and safety.

10. **How do you manage multiple environments (e.g., dev, staging, prod) in Terraform?**
    *Answer*: Common approaches include using Terraform Workspaces (which isolate state within the same configuration) or using directory structures (separate directories for each environment with their own state backends) combined with reusable modules. The directory structure is generally preferred for complete isolation in production.
