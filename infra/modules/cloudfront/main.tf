locals {
  bucket_name= "${var.application_name}-s3"
  origin_id= "${var.application_name}-front-origin"
}

# the origin bucket
resource "aws_s3_bucket" "data-app-s3" {
    tags = {
      "Name" = local.bucket_name
      "Project" = "Feth"
      "Function" = "origin s3 bucket for the CloudFront distribution. hosts the frontend static files for the ${var.application_name} app."
    }
    region = var.region
    bucket = local.bucket_name
    force_destroy = true
    
}

resource "aws_cloudfront_distribution" "data-app-front" {
    aliases = [  ]
    origin {
      domain_name = aws_s3_bucket.data-app-s3.bucket_domain_name
      origin_id = local.origin_id
      origin_access_control_id = aws_cloudfront_origin_access_control.data-app-oac.id
    }
    default_root_object = "index.html"
    price_class = "PriceClass_200"
    restrictions {
      geo_restriction {
        locations = [ "IE", "EG", "NL", "US" ]
        restriction_type = "whitelist"
      }
    }
    default_cache_behavior {
        allowed_methods = ["HEAD", "DELETE", "POST", "GET", "OPTIONS", "PUT", "PATCH"]
        cached_methods = [ "GET", "HEAD" ]
        viewer_protocol_policy = "redirect-to-https"
        target_origin_id = local.origin_id
        cache_policy_id = "658327ea-f89d-4fab-a63d-7e88639e58f6" # CachingOptimized
    }
    viewer_certificate {
      cloudfront_default_certificate = true
    }
    enabled = true
}


data "aws_iam_policy_document" "bucket-policy-body" {
    statement {
        sid = "AllowCloudFrontReadWrite"
        effect = "Allow"
        actions = [ "s3:GetObject", "s3:PutObject" ]
        resources = ["${aws_s3_bucket.data-app-s3.arn}/*"]

        principals {
          type = "Service"
          identifiers = ["cloudfront.amazonaws.com"]
        }
        condition {
          test = "StringEquals"
          variable = "AWS:SourceArn"
          values = [ aws_cloudfront_distribution.data-app-front.arn ]
        }
    }
}

resource "aws_s3_bucket_policy" "bucket-policy" {
  bucket = aws_s3_bucket.data-app-s3.bucket
  policy= data.aws_iam_policy_document.bucket-policy-body.json
}

resource "aws_cloudfront_origin_access_control" "data-app-oac" {
    name = "${var.application_name}-oac"
    origin_access_control_origin_type = "s3"
    signing_behavior = "always"
    signing_protocol = "sigv4"
  
}