output "alb_tgrp_web_arn" {
    value = aws_alb_target_group.collector-backend-target-web.arn
}
output "alb_tgrp_api_arn" {
    value = aws_alb_target_group.collector-backend-target-api.arn
}

output "app_dns" {
    value = aws_alb.collector-alb.dns_name
    description = "url to reach the ecs service after deployment"
  
}

output "alb_id" {
    value = aws_alb.collector-alb.id
}