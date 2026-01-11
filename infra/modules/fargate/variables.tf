variable "container_name" {
    type = string
    default = "speech-collector-backend"
    description = "backend container name for the ecs service"
}

variable "aws_profile" {
    type = string
  
}

variable "region" {
    type = string
  
}

variable "application_name" {
    type = string
}

variable "project_name" {
    type = string
}

variable "backend_port" {
    type = number
    default = 8500
    description = "the backend port for ingress frontend calls"
  
}

variable "bucket_name" {
    type= string
}

variable "alb_tgrp_web_arn" {
    type = string
}
variable "alb_tgrp_api_arn" {
    type = string
}
variable "image_registery" {
    type= string
    default = "436399611457.dkr.ecr.eu-central-1.amazonaws.com"
}
variable "backend_image" {
    type = string
    default = "speech-collector"
    description = "the container image for the backend app"
}

variable "backend_image_tag" {
    type = string
    default = "amd"
    description = "image tag for the backend container"
}

variable "secgrp_id" {
    type = string
  
}

variable "subnets_ids" {
    type = list(string)
}

variable "db_pass_file" {
    type = string
    sensitive = true
    default = "/run/secrets/db_password"
    description = "path to secret file within docker"
}

variable "db_root_pass_file" {
    type = string
    sensitive = true
    default = "/run/secrets/db_root_password"
    description = "path to secret file within docker"
}
variable "aws_access_id_file" {
    type = string
    sensitive = true
    default = "/run/secrets/aws_access_id"
    description = "path to secret file within docker"
}
variable "aws_secret_file" {
    type = string
    sensitive = true
    default = "/run/secrets/aws_access_secret"
    description = "path to secret file within docker"
}
variable "hf_token_file" {
    type = string
    sensitive = true
    default = "/run/secrets/hf_token"
    description = "path to secret file within docker"
}
variable "hf_repo" {
    type = string
    sensitive = false
    default = "feth-data-force"
    description = "hugging face remote data export repo"
}

variable "db_host" {
    type = string
}
variable "db_name" {
    type = string
}

variable "cf_dns" {
    type = string
}

variable "cors_regex" {
    type = string
    default = "^https?://(localhost:\\d{2,4}|[\\w.-]+\\.cloudfront\\.net)$"
}

variable "router_prefix" {
    type = string
    default = "/api"
}