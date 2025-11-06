module "vpc" {
  source = "./modules/vpc"
}

module "fargate" {
  source           = "./modules/fargate"
  region           = module.vpc.region
  secgrp_id        = module.vpc.secgrp_id
  subnets_ids      = module.vpc.subnets_ids
  aws_profile      = module.vpc.aws_profile
  application_name = module.vpc.application_name
  project_name     = module.vpc.project_name
  bucket_name      = module.vpc.bucket_name
  alb_tgrp_web_arn = module.alb.alb_tgrp_web_arn
  alb_tgrp_api_arn = module.alb.alb_tgrp_api_arn
  db_host          = module.aurora.db_host
  db_name          = module.aurora.db_name
  depends_on       = [ module.vpc, module.ssm, module.aurora  ]
} 

module "alb" {
  source           = "./modules/alb"
  vpc_id           = module.vpc.vpc_id
  secgrp_id        = module.vpc.secgrp_id
  subnets_ids      = module.vpc.subnets_ids
  region           = module.vpc.region
  aws_profile      = module.vpc.aws_profile
  application_name = module.vpc.application_name
  project_name     = module.vpc.project_name
  backend_port     = module.vpc.backend_port
  depends_on = [ module.vpc ]
}

module "ssm" {
  source = "./modules/ssm"
  region           = module.vpc.region
  aws_profile      = module.vpc.aws_profile
  application_name = module.vpc.application_name
  project_name     = module.vpc.project_name
  depends_on = [ module.vpc ]
}

module "aurora" {
  source = "./modules/aurora"
  region               = module.vpc.region
  aws_profile          = module.vpc.aws_profile
  application_name     = module.vpc.application_name
  project_name         = module.vpc.project_name
  backend_port         = module.vpc.backend_port
  bucket_name          = module.vpc.bucket_name
  db_root_pass_value   = module.ssm.collector-db-root-pass-value
  db_secgrp_id         = module.vpc.db_secgrp_id
  db_subnet_grp_name   = module.vpc.db_subnet_grp_name
  db_port              = module.vpc.db_port
  depends_on           = [ module.vpc, module.ssm ]
}

module "cloudfront" {
  source           = "./modules/cloudfront"
  region           = module.vpc.region
  aws_profile      = module.vpc.aws_profile
  application_name = module.vpc.application_name
  project_name     = module.vpc.project_name
  backend_port     = module.vpc.backend_port
  bucket_name      = module.vpc.bucket_name
  depends_on       = [ module.vpc ]
}
