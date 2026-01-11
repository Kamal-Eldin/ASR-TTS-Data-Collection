resource "aws_ssm_parameter" "collector-db-pass" {
    name = "MYSQL_PASSWORD"
    region = var.region
    type = "SecureString"
    value = var.MYSQL_PASSWORD
}

resource "aws_ssm_parameter" "collector-db-root-pass" {
    name = "MYSQL_ROOT_PASSWORD"
    region = var.region
    type = "SecureString"
    value = var.MYSQL_ROOT_PASSWORD
}

resource "aws_ssm_parameter" "collector-hf-token" {
    name = "HUGGINGFACE_TOKEN"
    region = var.region
    type = "SecureString"
    value = var.HF_TOKEN
}