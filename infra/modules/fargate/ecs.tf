resource "aws_ecs_cluster" "data-app-ecs-cluster" {
    name = "${var.application_name}-ecs-cluster"
    region = var.region
    
    configuration {
      execute_command_configuration {
        logging = "OVERRIDE"
        log_configuration {
          cloud_watch_log_group_name = aws_cloudwatch_log_group.data-app-ecs-watch-grp.name
          s3_bucket_name = var.bucket_name
          s3_key_prefix = "./ecs_logs"
        }
      }
    }
}

resource "aws_ecs_service" "data-app-ecs-service" {
    name = "${var.application_name}-ecs-service"
    cluster = aws_ecs_cluster.data-app-ecs-cluster.id
    # iam_role = aws_iam_role.data-app-ecs-role.arn # should not be configured if network is awsvpc on task definition
    availability_zone_rebalancing = "ENABLED"
    deployment_minimum_healthy_percent = 100
    enable_execute_command = true
    launch_type = "FARGATE"
    desired_count = 1
    load_balancer {
      target_group_arn = var.alb_tgrp_arn
      container_name = var.container_name
      container_port = var.backend_port
    }
    network_configuration {
        security_groups = [ var.secgrp_id ]
        subnets = var.subnets_ids
        assign_public_ip = true
    }
    
    scheduling_strategy = "REPLICA" # only option with FARGATE
    task_definition = aws_ecs_task_definition.data-app-ecs-task.arn
    depends_on = [ aws_ecs_task_definition.data-app-ecs-task, aws_iam_role_policy_attachment.data-app-ecs-role-attachment, aws_iam_role.data-app-ecs-role]
}

resource "aws_ecs_task_definition" "data-app-ecs-task" {
    family = "${var.application_name}-ecs-task"
    region = var.region
    task_role_arn = aws_iam_role.data-app-ecs-role.arn
    requires_compatibilities = [ "FARGATE" ]
    execution_role_arn = aws_iam_role.data-app-ecs-role.arn
    cpu = "2048"
    memory = "8192"
    network_mode = "awsvpc"  # required for containers on ecs FARGATE
    container_definitions =jsonencode(local.container_defs)
    depends_on = [ aws_ecs_cluster.data-app-ecs-cluster ]


}

locals {
    container_defs= [
        {
            name= var.container_name
            # image= "${var.image_registery}/${var.backend_image}:${var.backend_image_tag}"
            image= "nginxdemos/hello:0.4"
            portMappings= [
                {
                    containerPort= var.backend_port
                    protocol= "TCP"
                    hostPort=var.backend_port


                }
            ]
            # restartPolicy = {
            #         enabled= true
            #         restartAttemptPeriod= 120
            #     }
            # environment = [
            #     {name= "HUGGINGFACE_TOKEN_FILE", value= "simple_code"},
            #     {name= "AWS_ACCESS_KEY_ID_FILE", value= "simple_code"},
            #     {name= "AWS_SECRET_ACCESS_KEY_FILE", value= "simple_code"},
            #     {name= "MYSQL_PASSWORD_FILE", value= "simple_code"}
            # ]
            # secrets= [
            #     {name= "hf_token", valuefrom= "simple_code"},
            #     {name= "aws_access_id", valuefrom= "simple_code"},
            #     {name= "aws_access_secret", valuefrom= "simple_code"},
            #     {name= "db_password", valuefrom= "simple_code"},
            # ]
            
        }
    ]
}



resource "aws_cloudwatch_log_group" "data-app-ecs-watch-grp" {
    region = var.region
    name = "${var.application_name}-watch-grp"
    log_group_class = "STANDARD"
    retention_in_days = 3
}

data "aws_iam_policy" "ecs-task-exec-policy" {
    name = "AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role" "data-app-ecs-role" {
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

resource "aws_iam_role_policy_attachment" "data-app-ecs-role-attachment" {
    policy_arn = data.aws_iam_policy.ecs-task-exec-policy.arn
    role = aws_iam_role.data-app-ecs-role.name
  
}