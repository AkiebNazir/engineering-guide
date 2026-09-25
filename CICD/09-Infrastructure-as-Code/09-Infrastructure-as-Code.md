# Chapter 09: Infrastructure as Code

## 🎯 Learning Objectives
By the end of this chapter, you will be able to:
- Understand what Infrastructure as Code (IaC) is and why it's essential for modern CI/CD.
- Differentiate between declarative and imperative IaC tools.
- Write and structure Terraform configurations for infrastructure provisioning.
- Integrate Terraform securely into CI/CD pipelines.
- Use Ansible for configuration management post-provisioning.
- Write IaC using general-purpose languages with Pulumi (Go/Python).
- Apply IaC best practices including state management, drift detection, and cost estimation.

## 📖 Introduction
Imagine trying to bake 1,000 identical cakes but doing it by hand, without a recipe, measuring ingredients by eye every single time. It's slow, error-prone, and the cakes will inevitably vary. Now imagine you have an automated baking machine that reads a precise, written recipe. You just update the recipe, feed it into the machine, and out comes a perfectly consistent cake.

Infrastructure as Code (IaC) is that recipe for your infrastructure. Instead of clicking through cloud consoles or running manual SSH commands to set up servers and networks, you write code that defines your desired state. Your CI/CD pipelines then execute this code, ensuring your environments (Dev, Staging, Prod) are consistent, version-controlled, and easily reproducible.

## 🔑 Key Terminology

| Term | Definition |
|------|------------|
| **IaC** | Infrastructure as Code; managing and provisioning infrastructure through machine-readable definition files. |
| **Declarative** | You define *what* the end state should be, and the tool figures out *how* to achieve it (e.g., Terraform, CloudFormation). |
| **Imperative** | You define *how* to achieve the state step-by-step (e.g., bash scripts, some Ansible usage). |
| **State File** | A file (often JSON) where IaC tools like Terraform keep track of the resources they manage. |
| **Drift** | When the actual state of infrastructure differs from the state defined in your code. |
| **GitOps** | A paradigm where Git is the single source of truth for declarative infrastructure and applications. |

## 🏗️ What IaC is and Why It's Critical for CI/CD

Before IaC, infrastructure was a bottleneck. CI/CD automates software delivery, but if the underlying servers, databases, and networks are provisioned manually, your delivery pipeline hits a wall.

IaC allows your infrastructure to move at the speed of software. It brings the benefits of software engineering (version control, automated testing, peer review) to operations. When infrastructure is code, you can test it in CI, review it in a Pull Request, and deploy it continuously.

### Declarative vs Imperative IaC

- **Declarative (Terraform, Pulumi):** "I want 3 servers and a load balancer." The tool creates, updates, or deletes resources to match your request.
- **Imperative (Bash, Chef):** "Create server 1. Create server 2. Create server 3. Create load balancer. Attach servers." If you run it twice without error handling, you might get 6 servers.

## 🌍 Terraform Fundamentals

Terraform by HashiCorp is the industry standard for declarative IaC.

- **Providers:** Plugins that interface with APIs (AWS, GCP, Azure, GitHub).
- **Resources:** Infrastructure objects (EC2 instances, S3 buckets, VPCs).
- **State:** Terraform's memory (`terraform.tfstate`). Never store this in Git; use remote backends (S3, GCS) with locking.
- **Plan:** A dry run showing what Terraform *will* do (`terraform plan`).
- **Apply:** Executing the plan to provision resources (`terraform apply`).

### Terraform Project Structure

```text
infrastructure/
├── environments/
│   ├── dev/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── backend.tf
│   └── prod/
│       ├── main.tf
│       ├── variables.tf
│       └── backend.tf
└── modules/
    └── web-app/
        ├── main.tf
        ├── outputs.tf
        └── variables.tf
```

### Writing Terraform Configs

Here is an example of creating a VPC and a Compute Instance to host a Go or Python app.

```hcl
# main.tf
provider "aws" {
  region = "us-west-2"
}

# Create a VPC
resource "aws_vpc" "app_vpc" {
  cidr_block = "10.0.0.0/16"
  tags = {
    Name = "AppVPC"
  }
}

# Subnet
resource "aws_subnet" "app_subnet" {
  vpc_id            = aws_vpc.app_vpc.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "us-west-2a"
}

# Security Group
resource "aws_security_group" "web_sg" {
  name        = "web_sg"
  description = "Allow HTTP and SSH traffic"
  vpc_id      = aws_vpc.app_vpc.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["1.2.3.4/32"] # Restrict SSH
  }
}

# Compute Instance
resource "aws_instance" "app_server" {
  ami           = "ami-0c55b159cbfafe1f0" # Amazon Linux 2
  instance_type = "t2.micro"
  subnet_id     = aws_subnet.app_subnet.id
  vpc_security_group_ids = [aws_security_group.web_sg.id]

  user_data = <<-EOF
              #!/bin/bash
              echo "Deploying Python/Go app here..."
              EOF

  tags = {
    Name = "AppServer"
  }
}
```

## 🚀 Terraform in CI/CD Pipelines

A standard GitOps workflow involves running `terraform plan` on Pull Requests so reviewers can see the proposed infrastructure changes, and `terraform apply` when merged to the main branch.

```yaml
# .github/workflows/terraform.yml
name: Terraform Pipeline

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  terraform:
    runs-on: ubuntu-latest
    env:
      AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
      AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Terraform
      uses: hashicorp/setup-terraform@v2
      
    - name: Terraform Init
      run: terraform init
      
    - name: Terraform Validate
      run: terraform validate
      
    - name: Terraform Plan
      if: github.event_name == 'pull_request'
      run: terraform plan -out=tfplan
      
    - name: Terraform Apply
      if: github.event_name == 'push'
      run: terraform apply -auto-approve
```

## ⚙️ Ansible Basics: Configuration Management

While Terraform excels at *provisioning* infrastructure (creating servers), Ansible excels at *configuration management* (configuring what's inside the servers).

- **Inventory:** Lists of servers to manage.
- **Playbooks:** YAML files defining the desired configuration.
- **Roles:** Reusable blocks of logic.

```yaml
# playbook.yml (Installing a Go App)
---
- name: Setup Go App Server
  hosts: webservers
  become: yes
  tasks:
    - name: Install Go
      yum:
        name: golang
        state: present

    - name: Copy app binary
      copy:
        src: ./myapp
        dest: /usr/local/bin/myapp
        mode: '0755'

    - name: Ensure app is running via systemd
      systemd:
        name: myapp
        state: started
        enabled: yes
```

## 💻 Pulumi: IaC with Real Programming Languages

Pulumi allows you to write IaC using general-purpose languages like Go, Python, TypeScript, etc. This enables loops, conditionals, and standard testing frameworks.

### Pulumi Python Example

```python
import pulumi
import pulumi_aws as aws

# Create an S3 Bucket
bucket = aws.s3.Bucket("my-app-bucket",
    acl="private",
    tags={
        "Environment": "Dev",
    })

# Export the name of the bucket
pulumi.export("bucket_name", bucket.id)
```

### Pulumi Go Example

```go
package main

import (
	"github.com/pulumi/pulumi-aws/sdk/v5/go/aws/s3"
	"github.com/pulumi/pulumi/sdk/v3/go/pulumi"
)

func main() {
	pulumi.Run(func(ctx *pulumi.Context) error {
		// Create an AWS resource (S3 Bucket)
		bucket, err := s3.NewBucket(ctx, "my-app-bucket", &s3.BucketArgs{
			Acl: pulumi.String("private"),
			Tags: pulumi.StringMap{
				"Environment": pulumi.String("Dev"),
			},
		})
		if err != nil {
			return err
		}

		// Export the name of the bucket
		ctx.Export("bucketName", bucket.ID())
		return nil
	})
}
```

## 🌩️ CloudFormation Overview

AWS CloudFormation is AWS's native IaC service. It uses JSON or YAML templates. While powerful within AWS, it's vendor-locked compared to Terraform or Pulumi.

## 🛡️ IaC Best Practices & Security

- **State Management:** Use remote backends (S3 + DynamoDB locking) for Terraform. Never commit state files to Git.
- **Testing IaC:**
  - `terraform validate`: Syntax checking.
  - `tflint`: Linter for Terraform.
  - `checkov` / `tfsec`: Static analysis for security misconfigurations.
- **Secrets Management:** Do not hardcode API keys or passwords. Use AWS Secrets Manager, HashiCorp Vault, or CI/CD secrets variables. Retrieve them at runtime or via data sources in IaC.
- **Drift Detection:** Run periodic CI jobs to check `terraform plan`. If it shows changes when no code was merged, someone modified infrastructure manually (drift).
- **Cost Estimation:** Integrate tools like **Infracost** in your CI pipeline. It analyzes your `terraform plan` and comments on the PR with how much the change will increase or decrease your cloud bill.

## 💡 Best Practices

- **DO** modularize your IaC. Build reusable modules for standard components.
- **DO** use GitOps. All changes must go through a Pull Request.
- **DON'T** manually edit infrastructure in the cloud console. It causes drift.
- **DON'T** put sensitive data (like DB passwords) in plain text IaC.

## 🔗 How This Connects
- **Previous Chapter:** (08-CI-CD-Tools-Deep-Dive) Understanding the CI tools that will run our IaC pipelines.
- **Next Chapter:** (10-Artifact-Management) Where we store the compiled binaries or Docker images that our infrastructure will pull and deploy.

## 📝 Chapter Summary

| Concept | Explanation |
|---------|-------------|
| **IaC** | Code defining infrastructure, version-controlled and deployed via CI/CD. |
| **Terraform** | Declarative tool to provision cloud resources using HCL. |
| **Ansible** | Imperative/Declarative configuration management for server internals. |
| **Pulumi** | IaC using standard programming languages (Go, Python). |
| **State** | The source of truth for managed resources; must be secured remotely. |

## ➡️ What's Next
Proceed to the exercises to get hands-on with Terraform and Ansible!
