resource "aws_alb_target_group" "collector-backend-target-api" {
    # name= "${var.application_name}-alb-target-80" # no name allows terraform to destroy and recreate with new name.
    protocol = "HTTP"
    port = var.backend_port
    target_type = "ip" # flexible targeting as opposed to fixed resource (instance id)
    vpc_id = var.vpc_id # specify the vpc (i.e., the cidar block where the target resources exist)
    region = var.region
    health_check {
        enabled = true
        interval = 10
    }
    lifecycle {
      create_before_destroy = true # ensures that the listener has a target group to point to.
    }
  
}
resource "aws_alb_target_group" "collector-backend-target-web" {
    # name= "${var.application_name}-alb-target-80" # no name allows terraform to destroy and recreate with new name.
    protocol = "HTTP"
    port = 80
    target_type = "ip" # flexible targeting as opposed to fixed resource (instance id)
    vpc_id = var.vpc_id # specify the vpc (i.e., the cidar block where the target resources exist)
    region = var.region
    health_check {
        enabled = true
        interval = 10
    }
    lifecycle {
      create_before_destroy = true # ensures that the listener has a target group to point to.
    }
  
}

resource "aws_alb" "collector-alb" {
    name = "${var.application_name}-alb"
    load_balancer_type = "application"
    subnets = var.subnets_ids # where should we place the alb instance itself (2 AV Zones required)
    security_groups = [var.secgrp_id]
    internal = false # internet-facing (exists in public subnet to be reachable by cloudfront)
}

resource "aws_alb_listener" "collector-web-listener" {
  region = var.region
  load_balancer_arn = aws_alb.collector-alb.arn
  protocol = "HTTP"
  port = 80
  default_action {
    type = "forward"
    target_group_arn = aws_alb_target_group.collector-backend-target-web.arn
  }


}
resource "aws_alb_listener" "collector-frontend-listener" {
  region = var.region
  load_balancer_arn = aws_alb.collector-alb.arn
  protocol = "HTTP"
  port = var.backend_port
  default_action {
    type = "forward"
    target_group_arn = aws_alb_target_group.collector-backend-target-api.arn
  }


}
 