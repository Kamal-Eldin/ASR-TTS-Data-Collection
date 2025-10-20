module "cloudfront" {
  source = "./modules/cloudfront"
}

module "fargate" {
  source = "./modules/fargate"
  region = module.cloudfront.region
  aws_profile = module.cloudfront.aws_profile
  application_name = module.cloudfront.application_name
  project_name = module.cloudfront.project_name
}

module "vpc" {
  source = "./modules/vpc"
  region = module.cloudfront.region
  aws_profile = module.cloudfront.aws_profile
  application_name = module.cloudfront.application_name
  project_name = module.cloudfront.project_name
  backend_port = module.fargate.backend_port
  }