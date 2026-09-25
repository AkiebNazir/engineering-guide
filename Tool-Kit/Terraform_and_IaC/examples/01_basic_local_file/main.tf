terraform {
  required_providers {
    local = {
      source  = "hashicorp/local"
      version = "~> 2.0"
    }
  }
}

resource "local_file" "hello_world" {
  filename = "${path.module}/hello.txt"
  content  = "Hello from Terraform! This file was created using Infrastructure as Code."
}
