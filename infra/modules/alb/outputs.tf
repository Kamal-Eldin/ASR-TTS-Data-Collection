output "alb_tgrp_web_arn" {
    value = aws_alb_target_group.collector-backend-target-web.arn
}
output "alb_tgrp_api_arn" {
    value = aws_alb_target_group.collector-backend-target-api.arn
}