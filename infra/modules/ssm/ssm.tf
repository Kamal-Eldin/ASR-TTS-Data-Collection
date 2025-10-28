resource "aws_ssm_parameter" "data-app-db-pass" {
    name = "MYSQL_PASSWORD"
    region = var.region
    type = "SecureString"
    value = data.local_sensitive_file.db-pass.content
}

resource "aws_ssm_parameter" "data-app-db-root-pass" {
    name = "MYSQL_ROOT_PASSWORD"
    region = var.region
    type = "SecureString"
    value = data.local_sensitive_file.db-root-pass.content
}

resource "aws_ssm_parameter" "data-app-hf-token" {
    name = "HUGGINGFACE_TOKEN"
    region = var.region
    type = "SecureString"
    value = data.local_sensitive_file.hf-token.content
}