resource "aws_ecs_cluster" "data-app-ecs-cluster" {
    name = "${var.application_name}-ecs-cluster"
    region = var.region
    
}