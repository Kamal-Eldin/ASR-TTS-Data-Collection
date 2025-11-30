output "backend_dns" {
  value = module.lambda.lambda_dns
}

output "cf_dns" {
  value = module.cloudfront.cloudfront_domain
}

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

output "backend_route" {
  value = module.lambda.backend_route
}

output "app_alias" {
  value = module.route.app_alias
}