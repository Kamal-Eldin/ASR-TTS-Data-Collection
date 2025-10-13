terraform {
  required_providers {
    aws = {
      source = "hashicorp/aws"
      version = "6.16.0"
    }
  }
}

provider "aws" {
    profile = "Feth-IAM"
    region = "eu-central-1"

}