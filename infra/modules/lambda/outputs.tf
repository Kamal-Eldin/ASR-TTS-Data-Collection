output "lambda_dns" {
    value = replace(aws_lambda_function_url.speech-collector-lambda-url.function_url, "/\\/$/", "")
}

output "lambda_vpc" {
    value = aws_lambda_function.speech-collector-lambda.vpc_config
}

output "backend_route" {
    value = var.backend_route
}