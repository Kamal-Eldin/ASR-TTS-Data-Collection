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

variable "db_root_pass_value" {
    type = string
}

variable "db_name" {
    type = string
    default = "tts_dataset_generator"
}

variable "db_port" {
    type= number
    default = 3306
}

variable "db_secgrp_id" {
    type = string
}

variable "db_subnet_grp_name" {
    type = string
}

variable "aurora_version" {
    type = string
    default= "8.0.mysql_aurora.3.10.1" 
}

