data "aws_route53_zone" "data-app-zone" {
    name = var.apex_zone  # voiceforce.click  -> zone apex
    private_zone = false

}