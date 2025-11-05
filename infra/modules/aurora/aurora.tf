resource "aws_rds_cluster" "collector-db-cluster" {
    # cluster_identifier = "${var.application_name}-aurora-cluster"
    cluster_identifier_prefix = var.application_name
    engine = "aurora-mysql"
    engine_mode = "provisioned" # for serverless v2
    engine_version = var.aurora_version
    availability_zones = ["${var.region}a"] # single AZ for cutting costs - no auto failover
    database_name = var.db_name
    master_password = var.db_root_pass_value
    master_username = "admin"
    apply_immediately = true
    backtrack_window = 0 # range of history 
    backup_retention_period = 1 # in days
    enabled_cloudwatch_logs_exports = [ "audit", "error", "general", "iam-db-auth-error", "instance" ]
    port = var.db_port

    serverlessv2_scaling_configuration {
        min_capacity = 0
        max_capacity = 1
        seconds_until_auto_pause = 1800 # 30 mins until db auto pauses #!!! pause still charges for storage (snapshots are cheaper)
        
    }
    lifecycle {
    ignore_changes = [availability_zones]
  }
    vpc_security_group_ids = [ var.db_secgrp_id  ]
    db_subnet_group_name = var.db_subnet_grp_name
    skip_final_snapshot = true
    # final_snapshot_identifier = "db-snap-${timestamp()}"
}


resource "aws_rds_cluster_instance" "collector-db-instance" {
    region = var.region
    availability_zone = "${var.region}a"
    # identifier = "${var.application_name}-aurora-instance"
    cluster_identifier = aws_rds_cluster.collector-db-cluster.id
    instance_class = "db.serverless"  # for serverless v2
    engine = "aurora-mysql"
    engine_version = var.aurora_version
    publicly_accessible = true
    apply_immediately = true
    count = 1
}
