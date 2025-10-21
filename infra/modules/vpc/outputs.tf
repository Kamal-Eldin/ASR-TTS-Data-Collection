output "vpc_id"{
    value = aws_vpc.data-app-vpc.id
}

output "secgrp_id" {
    value = aws_security_group.alb-secgrp.id
}

output "subnets_ids" {
    value = [aws_subnet.data-app-subnet-1.id, aws_subnet.data-app-subnet-2.id]
}