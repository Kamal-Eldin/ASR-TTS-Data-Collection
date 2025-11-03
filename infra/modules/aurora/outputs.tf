output "db_name" {
    value = var.db_name
}
output "db_port" {
    value = var.db_port
}

output "aurora_cluster_id" {
    value = aws_rds_cluster.collector-db-cluster.id
}

output "db_host" {
    value = aws_rds_cluster.collector-db-cluster.reader_endpoint
}