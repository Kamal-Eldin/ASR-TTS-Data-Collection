output "collector-db-pass-arn" {
    value = aws_ssm_parameter.collector-db-pass.arn
}
output "collector-db-pass-value" {
    value = aws_ssm_parameter.collector-db-pass.value
}
output "collector-db-root-pass-arn" {
    value = aws_ssm_parameter.collector-db-root-pass.arn
}
output "collector-db-root-pass-value" {
    value = aws_ssm_parameter.collector-db-root-pass.value
}

output "collector-hf-token-arn" {
    value = aws_ssm_parameter.collector-hf-token.arn
}
