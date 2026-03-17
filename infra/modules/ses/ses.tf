resource "aws_ses_domain_identity" "collector-domain-identity" {
    region = var.region
    domain = var.apex_zone
    
}

# SES domain verification token TXT DNS record Name: "_amazonses.<mydomain>.<purpose>", value: "<token>"
resource "aws_route53_record" "collector-ses-verification-record" {
    zone_id = data.aws_route53_zone.data-app-zone.id
    name= "_amazonses.${aws_ses_domain_identity.collector-domain-identity.domain}"
    records =[aws_ses_domain_identity.collector-domain-identity.verification_token]
    type= "TXT"
    ttl = "600"
  
}


resource "aws_ses_domain_identity_verification" "collector-ses-verification" {
    domain = aws_ses_domain_identity.collector-domain-identity.domain
    depends_on = [ aws_route53_record.collector-ses-verification-record]

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

# DKIM resource
resource "aws_ses_domain_dkim" "collector-dkim" {
    region = var.region
    domain = aws_ses_domain_identity.collector-domain-identity.domain
    depends_on = [ aws_ses_domain_identity.collector-domain-identity ]
}

# DKIM CNAME records
# token1._domainkey.example.com CNAME token1.dkim.amazonses.com
# token2._domainkey.example.com CNAME token2.dkim.amazonses.com
# token3._domainkey.example.com CNAME token3.dkim.amazonses.com

#dkim_tokens[count.index] returns one of 3 dkim_tokens
resource "aws_route53_record" "collector-dkim-record" {
    count = 3 # SES needs 3 public keys (CNAMES) for redundancy & rotation
    zone_id = data.aws_route53_zone.data-app-zone.id
    name    = "${aws_ses_domain_dkim.collector-dkim.dkim_tokens[count.index]}._domainKey.${aws_ses_domain_identity.collector-domain-identity.domain}"
    records = ["${aws_ses_domain_dkim.collector-dkim.dkim_tokens[count.index]}.dkim.amazonses.com"]
    type    = "CNAME"
    ttl     = "600"
}

# DMARC records
resource "aws_route53_record" "collector-dmarc-record" {
    zone_id = data.aws_route53_zone.data-app-zone.id
    type = "TXT"
    name = "_dmarc.${aws_ses_domain_identity.collector-domain-identity.domain}"
    records = ["v=DMARC1;p=reject;pct=100"]
    ttl = "600"
}