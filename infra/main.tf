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
  alb_tgrp_arn     = module.alb.alb_tgrp_arn
}

module "vpc" {
  source           = "./modules/vpc"
  region           = module.cloudfront.region
  aws_profile      = module.cloudfront.aws_profile
  application_name = module.cloudfront.application_name
  project_name     = module.cloudfront.project_name
  backend_port     = module.fargate.backend_port
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
