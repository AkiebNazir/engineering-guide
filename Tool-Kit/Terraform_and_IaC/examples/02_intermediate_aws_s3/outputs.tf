output "bucket_arn" {
  description = "The Amazon Resource Name of the bucket"
  value       = aws_s3_bucket.my_bucket.arn
}

output "bucket_domain_name" {
  value = aws_s3_bucket.my_bucket.bucket_regional_domain_name
}
