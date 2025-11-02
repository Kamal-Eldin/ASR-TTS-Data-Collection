output "cloudfront_domain" {
    value = aws_cloudfront_distribution.collector-front.domain_name
    description = "the cloudfront dist domain name which users should hit to reach the service"
}
output "bucket_domain_name" {
    value = aws_s3_bucket.collector-s3.bucket_domain_name
    description = "the domain name of the cloudfront s3 origin, to reach the s3, if public"
}
output "bucket_id" {
    value = aws_cloudfront_distribution.collector-front.id
    description = "the id of the cloudfront s3 origin bucket"
}
output "bucket_arn" {
    value = aws_cloudfront_distribution.collector-front.arn
    description = "the arn of the cloudfront s3 origin bucket"
  
}

output "bucket_name" {
    value = aws_s3_bucket.collector-s3.bucket
    description = "the name of the cloudfront s3 origin bucket"
  
}

output "region" {
    value = var.region
}

output "aws_profile" {
    value = var.aws_profile
}

output "application_name" {
    value = var.application_name
}

output "project_name" {
    value = var.project_name
}