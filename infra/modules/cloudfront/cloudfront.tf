locals {
  bucket_name             = "${var.application_name}-s3"
  frontend_origin         = "${var.application_name}-s3-origin"
  primary_backend_origin  = "${var.application_name}-alb-origin"
  failover_backend_origin = "${var.application_name}-lambda-origin"
  origin_grp_id           = "${var.application_name}-origin-group"
}

# the origin bucket
resource "aws_s3_bucket" "collector-s3" {
    tags = {
      "Name" = local.bucket_name
      "Project" = "Feth"
      "Function" = "origin s3 bucket for the CloudFront distribution. hosts the frontend static files for the ${var.application_name} app."
    }
    region = var.region
    bucket = local.bucket_name
    force_destroy = true
    
}

resource "aws_cloudfront_distribution" "collector-front" {
    aliases = [ var.apex_zone ]
    
    origin {
      domain_name = aws_s3_bucket.collector-s3.bucket_domain_name
      origin_id = local.frontend_origin
      origin_access_control_id = aws_cloudfront_origin_access_control.collector-oac.id
      origin_path = var.origin_path
    }

    # origin {
    #   domain_name = replace(var.lambda_dns, "/(https?://)|(/$)/", "")
    #   origin_id = local.failover_backend_origin
    #   custom_origin_config {
    #     origin_protocol_policy = "https-only"
    #     origin_ssl_protocols = ["TLSv1.2"]
    #     http_port = var.backend_port
    #     ip_address_type = "ipv4"
    #     https_port = 443
    #   } 
    # }

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
        target_origin_id = local.frontend_origin
        cache_policy_id = "658327ea-f89d-4fab-a63d-7e88639e58f6" # CachingOptimized
        # cache_policy_id = "4135ea2d-6df8-44a3-9df3-4b5a84be39ad"  # CachingDisabled (0 minTTL, 0 maxTTL)
        # default_ttl = 5

    }

    # ordered_cache_behavior {
    #     path_pattern = "/api/*"
    #     allowed_methods = ["HEAD", "DELETE", "POST", "GET", "OPTIONS", "PUT", "PATCH"]
    #     cached_methods = [ "GET", "HEAD" ]
    #     viewer_protocol_policy = "allow-all"
    #     target_origin_id = local.failover_backend_origin
    #     cache_policy_id = "4135ea2d-6df8-44a3-9df3-4b5a84be39ad" # CachingDisabled (0 minTTL, 0 maxTTL)
    # }
    viewer_certificate {
      cloudfront_default_certificate = false # disabled, mutually exclusive with acm_certificate_arn
      acm_certificate_arn = var.cf_validation_arn
      ssl_support_method = "sni-only"
    }
    enabled = true
}


# data "aws_acm_certificate" "url-cert" {
#     region = "us-east-1"
#     domain = "*.${var.apex_zone}"
#     statuses = [ "ISSUED" ]
# }

data "aws_iam_policy_document" "bucket-policy-body" {
    statement {
        sid = "AllowCloudFrontReadWrite"
        effect = "Allow"
        actions = [ "s3:GetObject", "s3:PutObject" ]
        resources = ["${aws_s3_bucket.collector-s3.arn}/*"]

        principals {
          type = "Service"
          identifiers = ["cloudfront.amazonaws.com"]
        }
        condition {
          test = "StringEquals"
          variable = "AWS:SourceArn"
          values = [ aws_cloudfront_distribution.collector-front.arn ]
        }
    }
}

resource "aws_s3_bucket_policy" "bucket-policy" {
  bucket = aws_s3_bucket.collector-s3.bucket
  policy= data.aws_iam_policy_document.bucket-policy-body.json
}

resource "aws_cloudfront_origin_access_control" "collector-oac" {
    name = "${var.application_name}-oac"
    origin_access_control_origin_type = "s3"
    signing_behavior = "always"
    signing_protocol = "sigv4"
  
}