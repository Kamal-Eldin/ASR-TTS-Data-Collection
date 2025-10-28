output "data-app-db-pass-arn" {
    value = aws_ssm_parameter.data-app-db-pass.arn
}

output "data-app-db-root-pass-arn" {
    value = aws_ssm_parameter.data-app-db-root-pass.arn
}

output "data-app-hf-token-arn" {
    value = aws_ssm_parameter.data-app-hf-token.arn
}