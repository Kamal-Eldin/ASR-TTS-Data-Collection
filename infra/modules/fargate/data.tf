data "aws_ssm_parameter" "collector-db-pass" {
    name= "MYSQL_PASSWORD"
    region = var.region
    with_decryption= true
}

data "aws_ssm_parameter" "collector-db-root-pass" {
    name= "MYSQL_ROOT_PASSWORD"
    region = var.region
    with_decryption= true
}

data "aws_ssm_parameter" "collector-hf-token" {
    name= "HUGGINGFACE_TOKEN"
    region = var.region
    with_decryption= true
}