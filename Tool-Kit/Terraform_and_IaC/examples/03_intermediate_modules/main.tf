module "frontend_bucket" {
  source      = "./modules/secure_s3"
  bucket_name = "my-frontend-assets-999"
  environment = "Prod"
}

module "backend_bucket" {
  source      = "./modules/secure_s3"
  bucket_name = "my-backend-logs-999"
  environment = "Prod"
}
