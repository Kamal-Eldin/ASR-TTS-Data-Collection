# output "ecs_dns" {
#   value = module.alb.app_dns
# }

# output "cf_dns" {
#   value = module.cloudfront.cloudfront_domain
# }

output "db_host" {
  value = module.aurora.db_host
}
output "backend_port" {
  value = var.backend_port
}

output "origin_path" {
  value = var.origin_path
}

output "lambda_url" {
 value = module.lambda.lambda_dns
}