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