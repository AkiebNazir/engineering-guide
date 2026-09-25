<Chapter 09: Infrastructure as Code>
<Exercise 5: Enterprise IaC — Workspaces, Remote State, and Pulumi 🔴>
## 🎯 Objective
Design a multi-environment configuration using Terraform Remote State and Workspaces. Contrast it with modern general-purpose language IaC using Pulumi (Python and Go).

## 📋 Prerequisites
- Deep understanding of IaC concepts
- Familiarity with Python and Go programming languages

## 📝 Instructions
This is a multi-part conceptual exercise for an enterprise architecture.

**Part 1: Terraform Remote State and Workspaces**
1. Write a `backend.tf` configuring an AWS S3 backend with DynamoDB state locking.
2. Write a `main.tf` that changes the region based on the active Terraform workspace (e.g., `us-east-1` for dev, `us-west-2` for prod).

**Part 2: Pulumi in Python**
1. Write a Pulumi Python program (`__main__.py`) that creates an S3 bucket and exports its name.

**Part 3: Pulumi in Go**
1. Write a Pulumi Go program (`main.go`) that achieves the exact same S3 bucket creation.

## 💡 Hints
- In Terraform, you access the current workspace using `terraform.workspace`. Use a `locals` block to map workspaces to regions.
- Pulumi uses standard language SDKs. Import the Pulumi AWS SDK to interact with resources.

## ✅ Expected Output / Solution

### Part 1: Terraform Enterprise Setup

**`backend.tf`**
```hcl
terraform {
  backend "s3" {
    bucket         = "my-enterprise-tf-state-bucket"
    key            = "app/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-state-lock"
  }
}
```

**`main.tf`**
```hcl
locals {
  region_map = {
    "default" = "us-east-1"
    "dev"     = "us-east-1"
    "prod"    = "us-west-2"
  }
  
  # Select region based on active workspace
  active_region = lookup(local.region_map, terraform.workspace, "us-east-1")
}

provider "aws" {
  region = local.active_region
}

resource "aws_s3_bucket" "app_bucket" {
  bucket = "enterprise-app-bucket-${terraform.workspace}"
}
```

---

### Part 2: Pulumi with Python
With Pulumi, you can use general-purpose languages. This allows standard testing (e.g., pytest) and logic (loops, classes).

**`__main__.py`**
```python
import pulumi
import pulumi_aws as aws

# Create an AWS resource (S3 Bucket)
bucket = aws.s3.Bucket("enterprise-app-bucket",
    acl="private",
    tags={
        "Environment": pulumi.get_stack(), # Stack is Pulumi's equivalent to Workspaces
        "ManagedBy": "Pulumi"
    })

# Export the name of the bucket
pulumi.export("bucket_name", bucket.id)
```

---

### Part 3: Pulumi with Go
Go offers strong typing and excellent concurrency, making it a great choice for platform engineering teams.

**`main.go`**
```go
package main

import (
	"github.com/pulumi/pulumi-aws/sdk/v6/go/aws/s3"
	"github.com/pulumi/pulumi/sdk/v3/go/pulumi"
)

func main() {
	pulumi.Run(func(ctx *pulumi.Context) error {
		// Create an AWS resource (S3 Bucket)
		bucket, err := s3.NewBucket(ctx, "enterprise-app-bucket", &s3.BucketArgs{
			Acl: pulumi.String("private"),
			Tags: pulumi.StringMap{
				"Environment": pulumi.String(ctx.Stack()),
				"ManagedBy":   pulumi.String("Pulumi"),
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

## 🧠 Key Takeaway
Enterprise IaC requires robust state management to prevent team conflicts (State Locking via DynamoDB) and disaster (Remote State via S3). While Terraform's HCL is declarative and standard, tools like Pulumi offer expressive capabilities by utilizing loops, conditionals, and standard testing libraries of Go and Python, bridging the gap between application developers and platform engineers.
