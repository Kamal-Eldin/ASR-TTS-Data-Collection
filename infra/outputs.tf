output "ecs_dns" {
  value = module.alb.app_dns
}

output "cf_dns" {
  value = module.cloudfront.cloudfront_domain
}

output "backend_port" {
  value = var.backend_port
}

output "origin_path" {
  value = var.origin_path
}