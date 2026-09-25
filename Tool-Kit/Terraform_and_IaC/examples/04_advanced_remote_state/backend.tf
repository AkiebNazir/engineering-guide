terraform {
  # This block tells Terraform NOT to create a local terraform.tfstate file.
  # Instead, push it to an AWS S3 bucket.
  backend "s3" {
    bucket         = "my-company-terraform-state-bucket"
    key            = "production/infrastructure.tfstate"
    region         = "us-east-1"
    
    # DynamoDB table for State Locking. 
    # Prevents two engineers from running `terraform apply` at the exact same time.
    dynamodb_table = "terraform-state-locks"
    encrypt        = true
  }
}
