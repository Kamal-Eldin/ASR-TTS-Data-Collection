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

variable "db_port" {
    type = number
    default = 3306
}