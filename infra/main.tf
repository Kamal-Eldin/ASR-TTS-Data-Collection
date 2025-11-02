module "cloudfront" {
  source = "./modules/cloudfront"
}

module "fargate" {
  source           = "./modules/fargate"
  region           = module.cloudfront.region
  secgrp_id        = module.vpc.secgrp_id
  subnets_ids      = module.vpc.subnets_ids
  aws_profile      = module.cloudfront.aws_profile
  application_name = module.cloudfront.application_name
  project_name     = module.cloudfront.project_name
  bucket_name      = module.cloudfront.bucket_name
  alb_tgrp_web_arn = module.alb.alb_tgrp_web_arn
  alb_tgrp_api_arn = module.alb.alb_tgrp_api_arn
  depends_on = [ module.ssm ]
} 

module "vpc" {
  source           = "./modules/vpc"
  region           = module.cloudfront.region
  aws_profile      = module.cloudfront.aws_profile
  application_name = module.cloudfront.application_name
  project_name     = module.cloudfront.project_name
  backend_port     = module.fargate.backend_port
  db_name          = module.aurora.db_name
  db_port          = module.aurora.db_port
}

module "alb" {
  source           = "./modules/alb"
  vpc_id           = module.vpc.vpc_id
  secgrp_id        = module.vpc.secgrp_id
  subnets_ids      = module.vpc.subnets_ids
  region           = module.cloudfront.region
  aws_profile      = module.cloudfront.aws_profile
  application_name = module.cloudfront.application_name
  project_name     = module.cloudfront.project_name
  backend_port     = module.fargate.backend_port
}

module "ssm" {
  source = "./modules/ssm"
  region           = module.cloudfront.region
  aws_profile      = module.cloudfront.aws_profile
  application_name = module.cloudfront.application_name
  project_name     = module.cloudfront.project_name
}


module "aurora" {
  source = "./modules/aurora"
  region               = module.cloudfront.region
  aws_profile          = module.cloudfront.aws_profile
  application_name     = module.cloudfront.application_name
  project_name         = module.cloudfront.project_name
  backend_port         = module.fargate.backend_port
  bucket_name          = module.cloudfront.bucket_name
  db_root_pass_value   = module.ssm.collector-db-root-pass-value
  db_secgrp_id         = module.vpc.db_secgrp_id
  db_subnet_grp_name   = module.vpc.db_subnet_grp_name
}
