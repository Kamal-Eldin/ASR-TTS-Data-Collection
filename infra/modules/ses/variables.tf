
variable "application_name" {
    type = string
}

variable "region" {
    type = string
}

variable "aws_profile" {
    type = string

}

variable "project_name" {
    type = string
}

variable "bucket_name" {
    type = string
}

variable "apex_zone" {
  type = string
}

variable "mailfrom_subdomain" {
  type = string
  default = "noreply"
}

variable "mx_priority" {
    type = number
    default = 10
  
}

variable "spf_all_policy" {
    type = string
    default = "-all"
}