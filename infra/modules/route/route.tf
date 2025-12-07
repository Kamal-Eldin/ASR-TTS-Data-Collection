data "aws_route53_zone" "data-app-zone" {
    name = var.apex_zone  # voiceforce.click  -> zone apex
    private_zone = false

}

resource "aws_acm_certificate" "app_acm" {
    domain_name = var.apex_zone
    subject_alternative_names = ["*.${var.apex_zone}"]
    validation_method = "DNS"

    lifecycle {
      create_before_destroy = true
    }
}



resource "aws_route53_record" "cloudfront_alias" {
  zone_id = data.aws_route53_zone.data-app-zone.zone_id
  name    = var.apex_zone
  type    = "A"

  alias {
    name                   = var.cf_dns
    zone_id                = var.cf_zone  # CloudFront's hosted zone ID
    evaluate_target_health = false
  }
}

resource "aws_route53_record" "cert_validation" {

    for_each = {
        for v_op in aws_acm_certificate.app_acm.domain_validation_options: v_op.domain_name => {
            name = v_op.resource_record_name
            record = v_op.resource_record_value
            type = v_op.resource_record_type
            zone_id = data.aws_route53_zone.data-app-zone.id
        }
    }
    allow_overwrite = true
    name            = each.value.name
    records         = [each.value.record]
    ttl             = 60
    type            = each.value.type
    zone_id         = data.aws_route53_zone.data-app-zone.id
}

resource "aws_acm_certificate_validation" "app_acm_validation" {
    certificate_arn = aws_acm_certificate.app_acm.arn
    validation_record_fqdns = [ for record in aws_route53_record.cert_validation : record.fqdn ]

}

