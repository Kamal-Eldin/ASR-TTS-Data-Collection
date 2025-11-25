output "lambda_dns" {
    value = aws_lambda_function_url.speech-collector-lambda-url.function_url
}

output "lambda_vpc" {
    value = aws_lambda_function.speech-collector-lambda.vpc_config
}