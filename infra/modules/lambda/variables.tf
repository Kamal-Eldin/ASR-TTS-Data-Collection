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
  
}
variable "bucket_name" {
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

variable "db_host" {
    type = string
}
variable "db_name" {
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

variable "cf_dns" {
    type = string
}