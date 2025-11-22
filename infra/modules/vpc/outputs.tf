output "region" {
    value = var.region
}

output "aws_profile" {
    value = var.aws_profile
}

output "application_name" {
    value = var.application_name
}

output "project_name" {
    value = var.project_name
}


output "vpc_id"{
    value = aws_vpc.collector-vpc.id
}

output "secgrp_id" {
    value = aws_security_group.alb-secgrp.id
}
output "lambda_secgrp_id" {
    value = aws_security_group.lambda-secgrp.id
}


output "subnets_ids" {
    value = [aws_subnet.collector-subnet-1.id, aws_subnet.collector-subnet-2.id]
}

output "db_secgrp_id" {
    value = aws_security_group.collector-db-secgrp.id
}


output "db_subnet_grp_name" {
    value = aws_db_subnet_group.collector-db-subnet-group.name
}

output "db_port" {
    value = var.db_port
}

output "backend_port" {
    value = var.backend_port
}

output "bucket_name" {
    value = var.bucket_name
}

