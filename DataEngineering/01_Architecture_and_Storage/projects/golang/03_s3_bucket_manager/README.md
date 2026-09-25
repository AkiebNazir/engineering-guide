# 03_s3_bucket_manager

This script demonstrates basic S3 operations using the AWS Go SDK v2.

## How to Run

1. Initialize Go module:
   ```bash
   go mod init s3manager
   ```
2. Install dependencies:
   ```bash
   go get github.com/aws/aws-sdk-go-v2/config
   go get github.com/aws/aws-sdk-go-v2/service/s3
   ```
3. Run the script:
   ```bash
   go run main.go
   ```
   *(Note: The actual AWS calls are commented out to prevent unintended charges or errors if AWS credentials are not configured).*
