module "vpc" {
  source = "./modules/vpc"
}

module "efs" {
  source = "./modules/efs"
  region           = var.region
  aws_profile      = var.aws_profile
  application_name = var.application_name
  project_name     = var.project_name
  subnets_ids      = module.vpc.subnets_ids
  efs-secgrp_id    = module.vpc.efs_secgrp_id

  depends_on       = [ module.vpc ]
}

module "lambda" {
  source = "./modules/lambda"
  cf_dns           = "localhost:8500"
  region           = var.region
  aws_profile      = var.aws_profile
  application_name = var.application_name
  project_name     = var.project_name
  bucket_name      = var.bucket_name
  backend_port     = var.backend_port
  db_host          = module.aurora.db_host
  db_name          = module.aurora.db_name
  lambda-secgrp_id = module.vpc.lambda_secgrp_id
  subnets_ids      = module.vpc.subnets_ids
  efs_access_arn   = module.efs.efs_access_arn
  
  depends_on       = [ module.vpc, module.ssm, module.aurora, module.efs ]
}

# module "fargate" {
#   source           = "./modules/fargate"
#   region           = var.region
#   aws_profile      = var.aws_profile
#   application_name = var.application_name
#   project_name     = var.project_name
#   bucket_name      = var.bucket_name
#   secgrp_id        = module.vpc.secgrp_id
#   subnets_ids      = module.vpc.subnets_ids
#   alb_tgrp_web_arn = module.alb.alb_tgrp_web_arn
#   alb_tgrp_api_arn = module.alb.alb_tgrp_api_arn
#   db_host          = module.aurora.db_host
#   db_name          = module.aurora.db_name
#   cf_dns           = module.cloudfront.cloudfront_domain
#   depends_on       = [ module.vpc, module.ssm, module.aurora, module.cloudfront ]
# } 

# module "alb" {
#   source           = "./modules/alb"
#   vpc_id           = module.vpc.vpc_id
#   secgrp_id        = module.vpc.secgrp_id
#   subnets_ids      = module.vpc.subnets_ids
#   region           = var.region
#   aws_profile      = var.aws_profile
#   application_name = var.application_name
#   project_name     = var.project_name
#   backend_port     = var.backend_port
#   cf_dns           = module.cloudfront.cloudfront_domain
#   depends_on = [ module.vpc ]
# }

module "ssm" {
  source = "./modules/ssm"
  region              = var.region
  aws_profile         = var.aws_profile
  application_name    = var.application_name
  project_name        = var.project_name
  HF_TOKEN            = var.HF_TOKEN
  MYSQL_PASSWORD      = var.MYSQL_PASSWORD
  MYSQL_ROOT_PASSWORD = var.MYSQL_ROOT_PASSWORD

  depends_on = [ module.vpc ]
}

module "aurora" {
  source = "./modules/aurora"
  region               = var.region
  aws_profile          = var.aws_profile
  application_name     = var.application_name
  project_name         = var.project_name
  backend_port         = var.backend_port
  bucket_name          = var.bucket_name
  db_root_pass_value   = module.ssm.collector-db-root-pass-value
  db_secgrp_id         = module.vpc.db_secgrp_id
  db_subnet_grp_name   = module.vpc.db_subnet_grp_name
  db_port              = var.db_port
  
  depends_on           = [ module.vpc, module.ssm ]
}

# module "cloudfront" {
#   source           = "./modules/cloudfront"
#   region           = var.region
#   aws_profile      = var.aws_profile
#   application_name = var.application_name
#   project_name     = var.project_name
#   backend_port     = var.backend_port
#   bucket_name      = var.bucket_name
#   origin_path      = var.origin_path
#   alb_domain       = module.alb.app_dns
#   alb_id           = module.alb.alb_id
#   lambda_dns       = module.lambda.lambda_dns
#   depends_on       = [ module.vpc ]
# }
