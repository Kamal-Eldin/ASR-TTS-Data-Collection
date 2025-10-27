output "alb_tgrp_web_arn" {
    value = aws_alb_target_group.data-app-backend-target-web.arn
}
output "alb_tgrp_api_arn" {
    value = aws_alb_target_group.data-app-backend-target-api.arn
}