
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