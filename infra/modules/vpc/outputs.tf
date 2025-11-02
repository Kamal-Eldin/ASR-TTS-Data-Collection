output "vpc_id"{
    value = aws_vpc.collector-vpc.id
}

output "secgrp_id" {
    value = aws_security_group.alb-secgrp.id
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