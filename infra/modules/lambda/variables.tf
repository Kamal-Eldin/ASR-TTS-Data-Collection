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
    default = "^https?://(localhost:\\d+|[\\w-]+\\.cloudfront\\.net.?$|\\w*.?voiceforce.click.?$)"
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

variable "lambda-secgrp_id" {
    type = string
}

variable "subnets_ids" {
    type = list(string)
}

variable "cf_dns" {
    type = string
}

variable "root_dir" {
    type = string
    default = "/mnt/data"
    description = "root dir for EFS mount and consequently STORAGE_PATH env var"
}

variable "efs_access_arn" {
    type = string
}

variable "backend_route" {
    type = string
    default = ""
}

variable "ses_sender_email" {
    type        = string
    default     = ""
    description = "Verified SES sender address used for password-reset emails. Leave empty to disable email sending."
}

variable "frontend_url" {
    type        = string
    default     = ""
    description = "Base URL the password-reset email links back to. Falls back to the CloudFront domain if empty."
}