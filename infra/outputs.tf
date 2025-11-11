output "ecs_dns" {
  value = module.alb.app_dns
}

output "cf_dns" {
  value = module.cloudfront.cloudfront_domain
}