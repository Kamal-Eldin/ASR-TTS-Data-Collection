resource "aws_ses_domain_identity" "collector-domain-identity" {
    region = var.region
    domain = var.apex_zone
    
}

locals {
    mailform= "${var.mailfrom_subdomain}.${aws_ses_domain_identity.collector-domain-identity.domain}"
}

resource "aws_ses_domain_identity_verification" "collector-domain-identity-verification" {
    region = var.region
    domain = aws_ses_domain_identity.collector-domain-identity.domain
    depends_on = [ aws_ses_domain_identity.collector-domain-identity ]
}

resource "aws_ses_domain_mail_from" "collector-mail-from" {
    region = var.region
    domain = aws_ses_domain_identity.collector-domain-identity.domain
    mail_from_domain = "${var.mailfrom_subdomain}.${aws_ses_domain_identity.collector-domain-identity.domain}"
    behavior_on_mx_failure = "RejectMessage"
    depends_on = [ aws_ses_domain_identity.collector-domain-identity ]
}

# MAIL FROM MX records
resource "aws_route53_record" "collector-mx-records" {
    zone_id = data.aws_route53_zone.data-app-zone.id
    name = aws_ses_domain_mail_from.collector-mail-from.mail_from_domain
    type = "MX"
    ttl = "600"
    records = ["${var.mx_priority} feedback-smtp.${var.region}.amazonses.com"]

}

# MAIL FROM SPF TXT records

resource "aws_route53_record" "collector-spf-record" {
  zone_id = data.aws_route53_zone.data-app-zone.id
  name    = aws_ses_domain_mail_from.collector-mail-from.mail_from_domain
  type    = "TXT"
  ttl     = "600"
  records = ["v=spf1 include:amazonses.com ${var.spf_all_policy}"]
}

# DKIM CNAME records