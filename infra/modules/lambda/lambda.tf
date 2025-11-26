
locals {
    CORS_ORIGINS = ["http://${var.cf_dns}", "https://${var.cf_dns}" ]
}

resource "aws_cloudwatch_log_group" "collector-backend-watch-grp" {
    region = var.region
    name = "${var.application_name}-watch-grp"
    log_group_class = "STANDARD"
    retention_in_days = 3
}


resource "aws_iam_role" "lambda-execution-role" {
    name = "${var.application_name}-lambda-exec-role"
    assume_role_policy = data.aws_iam_policy_document.lambda-role-trust-policy.json # specify the role trust policy
}

resource "aws_iam_role_policy_attachment" "lambda-basic-execpolicy-attach" {
    policy_arn = data.aws_iam_policy.lambda-basic-exe-policy.arn
    role = aws_iam_role.lambda-execution-role.name
}

resource "aws_iam_role_policy_attachment" "lambda-ecrpolicy-attach" {
    policy_arn = data.aws_iam_policy.lambda-ecr-access-policy.arn
    role = aws_iam_role.lambda-execution-role.name
}


resource "aws_iam_role_policy_attachment" "lambda-net-policy-attach" {
    # policy_arn = aws_iam_policy.lambda-net-interface-policy.arn
    policy_arn = data.aws_iam_policy.lambda-vpc-access-policy.arn
    role = aws_iam_role.lambda-execution-role.name
}

resource "aws_iam_role_policy_attachment" "lambda-efs-policy-attach" {
    policy_arn = data.aws_iam_policy.lambda-efs-access.arn
    role = aws_iam_role.lambda-execution-role.name
}

resource "aws_lambda_function_url" "speech-collector-lambda-url" {
    region = var.region
    function_name = aws_lambda_function.speech-collector-lambda.function_name
    authorization_type = "NONE"
    cors {
      allow_origins = local.CORS_ORIGINS 
      allow_methods = [ "GET", "POST", "DELETE", "PUT", "PATCH" ]
      
    }
  
}

resource "aws_lambda_function" "speech-collector-lambda" {
    region = var.region
    function_name = "${var.application_name}-lambda-backend"
    package_type = "Image"
    role= aws_iam_role.lambda-execution-role.arn
    image_uri = "${var.image_registery}/${var.backend_image}:${var.backend_image_tag}"
    memory_size = 4096

    architectures = ["x86_64"] # see build an arm64 for better pricing

    environment {
        variables= {
            "MYSQL_PORT"            = "3306"
            "MYSQL_USER"            = "admin"
            "MYSQL_HOST"            = var.db_host
            "MYSQL_DATABASE"        = var.db_name
            "APP_PORT"              = tostring(var.backend_port)
            "BACKEND_URL"           = "http://localhost:${var.backend_port}"
            "VITE_BACKEND_URL"      = "http://localhost:${var.backend_port}"

            "AWS_EXPORT_KEY_ID"     = ""
            "AWS_EXPORT_KEY_SECRET" = ""
            "HF_EXPORT_TIMEOUT"     = "300"
            "S3_EXPORT_TIMEOUT"     = "300"
            "HUGGINGFACE_REPO"      = "feth-data-force"
                            
            "ROUTER_PREFIX"         = var.backend_route # empty string for single CF origin | /api for origin group failover setup
            "CORS_REGEX"            = var.cors_regex
            "STORAGE_PATH"          = "${var.root_dir}/recordings"
            "CORS_ORIGINS"          = "https://${var.cf_dns}, http://${var.cf_dns}"
            
            "HUGGINGFACE_TOKEN"= data.aws_ssm_parameter.collector-hf-token.value
            "MYSQL_PASSWORD"   = data.aws_ssm_parameter.collector-db-root-pass.value

            "AWS_LWA_READINESS_CHECK_PATH" = "/health"
            "AWS_LWA_PORT" = tostring(var.backend_port)
        }
    }
    
    ephemeral_storage {  # auto mapped to /tmp
        size = 8192
    }

    logging_config {
        log_format = "JSON"
        log_group =aws_cloudwatch_log_group.collector-backend-watch-grp.name
        system_log_level = "DEBUG"
        application_log_level = "TRACE" 
    }
    vpc_config {
        security_group_ids = [var.lambda-secgrp_id ]
        subnet_ids = [var.subnets_ids[0]]
    }

    file_system_config {
      arn = var.efs_access_arn
      local_mount_path = var.root_dir
    }

    timeout = 180  # 3 mins; minimum running time in secs 
}