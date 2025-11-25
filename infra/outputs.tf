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

output "lambda_vpc" {
  value = module.lambda.lambda_vpc
}
output "subnets_ids" {
    value = module.vpc.subnets_ids
}
output "efs-AZ" {
  value = module.efs.efs-AZ
}
output "subnet_1-AZ" {
    value = module.vpc.subnet_1-AZ
}
output "subnet_2-AZ" {
    value = module.vpc.subnet_2-AZ
}