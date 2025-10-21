resource "aws_alb_target_group" "data-app-backend-target" {
    name= "${var.application_name}-alb-target"
    protocol = "HTTP"
    port = var.backend_port
    target_type = "ip" # flexible targeting as opposed to fixed resource (instance id)
    vpc_id = var.vpc_id # specify the vpc (i.e., the cidar block where the target resources exist)
    region = var.region
    health_check {
        enabled = true
        interval = 10
    }

}

resource "aws_alb" "data-app-alb" {
    name = "${var.application_name}-alb"
    load_balancer_type = "application"
    subnets = var.subnets_ids # where should we place the alb instance itself (2 AV Zones required)
    security_groups = [var.secgrp_id]
    internal = false # internet-facing (exists in public subnet to be reachable by cloudfront)
    
}


resource "aws_alb_listener" "data-app-frontend-listener" {
  region = var.region
  load_balancer_arn = aws_alb.data-app-alb.arn
  protocol = "HTTP"
  port = var.backend_port
  default_action {
    type = "forward"
    target_group_arn = aws_alb_target_group.data-app-backend-target.arn
  }


}
