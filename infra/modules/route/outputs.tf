
output "app_alias" {
    value = aws_route53_record.cloudfront_alias.fqdn
}

output "cf_validation_arn" {
    value = aws_acm_certificate_validation.app_acm_validation.certificate_arn
}