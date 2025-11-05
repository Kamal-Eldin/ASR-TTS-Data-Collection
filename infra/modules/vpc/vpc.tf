resource "aws_vpc" "collector-vpc" {
    region = var.region
    enable_dns_hostnames = true
    cidr_block = "10.1.0.0/16" # [ 10.1.0.0 - 10.1.255.255 ]
    
    tags = {
      "Name" = "${var.application_name}-vpc"
      "Project"= var.project_name
      "Function"= "Isolates the data app backend deployment resources"
    }
}

resource "aws_subnet" "collector-subnet-1" {
    vpc_id = aws_vpc.collector-vpc.id
    region = var.region
    availability_zone = "${var.region}a"
    cidr_block = "10.1.0.0/20" # [10.1.0.0 - 10.1.15.255 ]
    map_public_ip_on_launch = true
  
}
resource "aws_subnet" "collector-subnet-2" {
    vpc_id = aws_vpc.collector-vpc.id
    region = var.region
    availability_zone = "${var.region}b"
    cidr_block = "10.1.16.0/20" # [10.1.16.0 - 10.1.31.255]
    map_public_ip_on_launch = true
  
}

resource "aws_security_group" "alb-secgrp" {
    name= "${var.application_name}-alb-secgrp"
    vpc_id = aws_vpc.collector-vpc.id
    region = var.region
    depends_on = [ aws_vpc.collector-vpc ]

}

resource "aws_vpc_security_group_ingress_rule" "backend-inbound-web" {
    # cidr_ipv4 = aws_vpc.collector-vpc.cidr_block
    cidr_ipv4 = "0.0.0.0/0"
    ip_protocol = "tcp"
    to_port = 80 # backend pre-configured port. embedded in frontend calls.
    from_port = 80
    security_group_id = aws_security_group.alb-secgrp.id
    depends_on = [ aws_security_group.alb-secgrp, aws_vpc.collector-vpc ]
}

resource "aws_vpc_security_group_ingress_rule" "backend-inbound-api" {
    # cidr_ipv4 = aws_vpc.collector-vpc.cidr_block
    cidr_ipv4 = "0.0.0.0/0"
    ip_protocol = "tcp"
    to_port = var.backend_port # backend pre-configured port. embedded in frontend calls.
    from_port = var.backend_port
    security_group_id = aws_security_group.alb-secgrp.id
    depends_on = [ aws_security_group.alb-secgrp, aws_vpc.collector-vpc ]
}

resource "aws_vpc_security_group_egress_rule" "backend-outbound" {
    cidr_ipv4 = "0.0.0.0/0"
    ip_protocol = "tcp"
    to_port = 65535
    from_port = 0
    security_group_id = aws_security_group.alb-secgrp.id
    depends_on = [ aws_security_group.alb-secgrp, aws_vpc.collector-vpc ]
}

resource "aws_internet_gateway" "collector-igw" {    
    vpc_id = aws_vpc.collector-vpc.id
    region = var.region
    depends_on = [ aws_vpc.collector-vpc ]

}

resource "aws_route_table" "collector-route-table" {
    region = var.region
    vpc_id = aws_vpc.collector-vpc.id
    depends_on = [ aws_vpc.collector-vpc, aws_internet_gateway.collector-igw ]
}

# local routes are created implicitly 
resource "aws_route" "collector-internet-route" {
    region = var.region
    destination_cidr_block = "0.0.0.0/0" # allow all outbound connections
    gateway_id = aws_internet_gateway.collector-igw.id
    route_table_id = aws_route_table.collector-route-table.id
    depends_on = [ aws_route_table.collector-route-table ]
}

resource "aws_route_table_association" "collector-rt-subnet-1" {
    route_table_id = aws_route_table.collector-route-table.id
    subnet_id = aws_subnet.collector-subnet-1.id
}

resource "aws_route_table_association" "collector-rt-subnet-2" {
    route_table_id = aws_route_table.collector-route-table.id
    subnet_id = aws_subnet.collector-subnet-2.id
}

resource "aws_security_group" "collector-db-secgrp" {
    vpc_id = aws_vpc.collector-vpc.id
    region = var.region
  
}

resource "aws_vpc_security_group_ingress_rule" "collector-db-ingress" {
    security_group_id = aws_security_group.collector-db-secgrp.id
    # cidr_ipv4 = aws_vpc.collector-vpc.cidr_block
    cidr_ipv4 = "0.0.0.0/0"
    from_port = var.db_port
    to_port = var.db_port
    ip_protocol = "TCP"

}

resource "aws_vpc_security_group_egress_rule" "collector-db-egress" {
    security_group_id = aws_security_group.collector-db-secgrp.id
    # cidr_ipv4 = aws_vpc.collector-vpc.cidr_block
    cidr_ipv4 = "0.0.0.0/0"
    from_port = var.db_port
    to_port = var.db_port
    ip_protocol = "TCP"

}

resource "aws_db_subnet_group" "collector-db-subnet-group" {
    name = "${var.application_name}-db-subnet-grp"
    subnet_ids = [aws_subnet.collector-subnet-1.id, aws_subnet.collector-subnet-2.id]
}
