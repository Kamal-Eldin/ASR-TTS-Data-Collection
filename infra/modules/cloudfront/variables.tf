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