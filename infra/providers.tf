terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "6.16.0"
    }
  }
}

provider "aws" {
  # profile = "Feth-IAM"
  region  = "eu-central-1"

}

terraform {
  backend "s3" {
    # profile = "Feth-IAM"
    bucket  = "feth-s3"
    key     = "terraform/speech-collector-state.tfstate"
    region  = "eu-central-1"
  }
}