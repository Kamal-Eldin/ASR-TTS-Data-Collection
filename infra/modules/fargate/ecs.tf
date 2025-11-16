resource "aws_ecs_cluster" "collector-ecs-cluster" {
    name = "${var.application_name}-ecs-cluster"
    region = var.region
    
    configuration {
      execute_command_configuration {
        logging = "OVERRIDE"
        log_configuration {
            cloud_watch_log_group_name = aws_cloudwatch_log_group.collector-ecs-watch-grp.name
            s3_bucket_name = var.bucket_name
            s3_key_prefix = "./ecs_logs"
        }
      }
    }
}

resource "aws_ecs_service" "collector-ecs-service" {
    name = "${var.application_name}-ecs-service"
    cluster = aws_ecs_cluster.collector-ecs-cluster.id
    # iam_role = aws_iam_role.collector-ecs-role.arn # should not be configured if network is awsvpc on task definition
    availability_zone_rebalancing = "ENABLED"
    deployment_minimum_healthy_percent = 100
    enable_execute_command = true
    launch_type = "FARGATE"
    desired_count = 1
    load_balancer {
        target_group_arn = var.alb_tgrp_web_arn
        container_name = var.container_name
        container_port = 80
    }
    load_balancer {
        target_group_arn = var.alb_tgrp_api_arn
        container_name = var.container_name
        container_port = var.backend_port
    }
    network_configuration {
        security_groups = [ var.secgrp_id ]
        subnets = var.subnets_ids
        assign_public_ip = true
    }
    
    scheduling_strategy = "REPLICA" # only option with FARGATE
    task_definition = aws_ecs_task_definition.collector-ecs-task.arn
    depends_on = [ aws_ecs_task_definition.collector-ecs-task, aws_iam_role_policy_attachment.collector-ecs-role-attachment, aws_iam_role.collector-ecs-role]
}

resource "aws_ecs_task_definition" "collector-ecs-task" {
    family = "${var.application_name}-ecs-task"
    region = var.region
    task_role_arn = aws_iam_role.collector-ecs-role.arn
    requires_compatibilities = [ "FARGATE" ]
    execution_role_arn = aws_iam_role.collector-ecs-role.arn
    cpu = "2048"
    memory = "8192"
    network_mode = "awsvpc"  # required for containers on ecs FARGATE
    container_definitions =jsonencode(local.container_defs)
    depends_on = [ aws_ecs_cluster.collector-ecs-cluster]

}

locals {
    CORS_ORIGINS = var.cf_dns
    container_defs= [
        {
            name= var.container_name
            image= "${var.image_registery}/${var.backend_image}:${var.backend_image_tag}"
            # image= "public.ecr.aws/nginx/nginx:trixie-perl"
            cpu: 2048
            portMappings= [
                {
                    containerPort= var.backend_port
                    protocol= "tcp"
                    hostPort=var.backend_port

                },
                {
                    containerPort= 80
                    protocol= "tcp"
                    hostPort=80
                }
            ],
            logConfiguration= {
                logDriver="awslogs"
                options= {
                    awslogs-region=var.region
                    awslogs-group=aws_cloudwatch_log_group.collector-ecs-watch-grp.name
                    awslogs-stream-prefix="feth" # resolves to prefix-name/container-name/ecs-task-id -> feth/speech-collector-backend/<task-id>
                    # aws-logs-datetime-format="[%b %d, %Y %I:%M:%S %p]" # disallowed by aws
                    mode="non-blocking"
                    max-buffer-size="25m" 
                }
            }
            restartPolicy = {
                    enabled= true
                    restartAttemptPeriod= 60 # minimum [60-1800] secs
                }
            environment = [
                {name= "MYSQL_PORT", value="3306"},
                {name= "MYSQL_USER", value="admin"},
                {name= "MYSQL_HOST", value=var.db_host},
                {name= "MYSQL_DATABASE", value=var.db_name},
                {name= "APP_PORT", value=tostring(var.backend_port)},
                {name= "BACKEND_URL", value="http://localhost:${var.backend_port}"},
                {name= "VITE_BACKEND_URL", value="http://localhost:${var.backend_port}"},

                {name= "MYSQL_PASSWORD_FILE", value= ""},
                {name= "HUGGINGFACE_TOKEN_FILE", value= ""},
                {name= "AWS_ACCESS_KEY_ID_FILE", value= ""},
                {name= "MYSQL_ROOT_PASSWORD_FILE", value= ""},
                {name= "AWS_SECRET_ACCESS_KEY_FILE",value= ""},
                {name= "HUGGINGFACE_REPO", value="feth-data-force"},
                {name= "HF_EXPORT_TIMEOUT", value="300"},
                {name= "S3_EXPORT_TIMEOUT", value="300"},
                
                {name= "CORS_ORIGINS", value="https://${local.CORS_ORIGINS}, http://${local.CORS_ORIGINS}"},
                {name= "CORS_REGEX"  , value=var.cors_regex},
                {name= "STORAGE_PATH", value="recordings"}


            ]
            secrets= [
                {name= "hf_token", valuefrom= data.aws_ssm_parameter.collector-hf-token.arn},
                {name= "db_password", valuefrom= data.aws_ssm_parameter.collector-db-pass.arn},
                # {name= "aws_access_id", valuefrom= "simple_code"},
                # {name= "aws_access_secret", valuefrom= "simple_code"}
            ]
            healthCheck={
                command= ["CMD-SHELL", "curl -f http://localhost:8500/health || exit 1"]
                interval = 10
                timeout= 30
                retries= 3
                startPeriod=120
            }
            workingDirectory= "/app/backend"
            command= ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8500"]

            
        }
    ]
}


resource "aws_cloudwatch_log_group" "collector-ecs-watch-grp" {
    region = var.region
    name = "${var.application_name}-watch-grp"
    log_group_class = "STANDARD"
    retention_in_days = 3
}

data "aws_iam_policy" "ecs-task-exec-policy" {
    name = "AmazonECSTaskExecutionRolePolicy"
}
data "aws_iam_policy" "ecs-ssm-read-policy" {
    name = "AmazonSSMReadOnlyAccess"
}

resource "aws_iam_policy" "ecs-ssm-exec-channel-policy" {
    name= "EcsSsmExecPermissions"
    description = "enables ecs to do container execs"
    policy = jsonencode({
        "Version": "2012-10-17",
        "Statement": [
            {
            "Effect": "Allow",
            "Action": [
                "ssmmessages:CreateControlChannel",
                "ssmmessages:CreateDataChannel",
                "ssmmessages:OpenControlChannel",
                "ssmmessages:OpenDataChannel"
                ],
            "Resource": "*"
            }
        ]
    }
    )
}

resource "aws_iam_policy" "ecs-allow-container-exec-policy" {
    name= "EcsContainerExecPermissions"
    description = "enables ecs to do container execs"
    policy = jsonencode({
        "Version": "2012-10-17",
        "Statement": [
            {
            "Effect": "Allow",
            "Action": [
                "ecs:ExecuteCommand"
                ],
            "Resource": "${aws_ecs_cluster.collector-ecs-cluster.arn}"
            }
        ]
    }
    )
}


resource "aws_iam_role" "collector-ecs-role" {
    name = "${var.application_name}-ecs-role"
    assume_role_policy = jsonencode({
      Version = "2012-10-17"
      Statement = [
        {
          Action = "sts:AssumeRole"
          Effect = "Allow"
          Principal = {
            Service = "ecs-tasks.amazonaws.com"
          }
        }
       ]
    })
}
resource "aws_iam_role_policy_attachment" "collector-ecs-ssm-channel-attachment" {
    policy_arn = aws_iam_policy.ecs-ssm-exec-channel-policy.arn
    role = aws_iam_role.collector-ecs-role.name
  
}
resource "aws_iam_role_policy_attachment" "collector-ecs-container-exec-attachment" {
    policy_arn = aws_iam_policy.ecs-allow-container-exec-policy.arn
    role = aws_iam_role.collector-ecs-role.name
  
}

resource "aws_iam_role_policy_attachment" "collector-ecs-role-attachment" {
    policy_arn = data.aws_iam_policy.ecs-task-exec-policy.arn
    role = aws_iam_role.collector-ecs-role.name
  
}
resource "aws_iam_role_policy_attachment" "collector-ecs-ssm-attachment" {
    policy_arn = data.aws_iam_policy.ecs-ssm-read-policy.arn
    role = aws_iam_role.collector-ecs-role.name
  
}