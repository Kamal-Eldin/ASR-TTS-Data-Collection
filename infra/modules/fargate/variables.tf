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
    type = number
    default = 0.1
    description = "image tag for the backend container"
}

variable "secgrp_id" {
    type = string
  
}

variable "subnets_ids" {
    type = list(string)
}