variable "vpc_id" {
    type = string
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
  
}

variable "secgrp_id" {
    type = string
}

variable "subnets_ids" {
    type = list(string)
}