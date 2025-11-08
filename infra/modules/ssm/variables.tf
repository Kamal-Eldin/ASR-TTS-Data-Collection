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