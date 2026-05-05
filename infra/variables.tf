variable "application_name" {
    type = string
    default = "speech-collector"
    description = "name of the speech data collection webapp."
}

variable "region" {
    type = string
    default = "eu-central-1"
    description = "default region for most activities directed to the app."
}

variable "aws_profile" {
    type = string
    default = "Feth-IAM"
    description = "aws profile to use for the provider and terraform remote state management."
  
}

variable "project_name" {
    type = string
    default= "Feth"
}

variable "db_port" {
    type = number
    default = 3306
}
variable "backend_port" {
    type = number
    default = 8500
}

variable "bucket_name" {
    default = "speech-collector-s3"
    description = "s3 bucket for cloudfront origin and aurora snapshots and logs"
  
}

variable "HF_TOKEN" {
    type = string
    sensitive = true
}
variable "MYSQL_ROOT_PASSWORD" {
    type = string
    sensitive = true
}

variable "MYSQL_PASSWORD" {
    type = string
    sensitive = true
}

variable "origin_path" {
    type = string
    default = "/frontend"
    sensitive = false
}

variable "apex_zone" {
    type = string
    default = "voiceforce.click"

}

variable "ses_sender_email" {
    type        = string
    default     = ""
    description = "Verified SES sender address used for password-reset emails. Leave empty to disable email sending."
}

variable "frontend_url" {
    type        = string
    default     = ""
    description = "Override for the URL embedded in password-reset emails. Falls back to the CloudFront domain if empty."
}