# resource "aws_alb_target_group" "name" {
#     name= "${var.application_name}-alb-target"
#     protocol = "TCP"
#     target_type = "alb"
#     vpc_id = aws_vpc.data-app-vpc.id
#     port = var.backend_port
#     region = var.region

# }


# resource "aws_alb" "name" {
#     name = "${var.application_name}-alb"

# }