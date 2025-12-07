output "efs-AZ" {
    value = aws_efs_file_system.data-app-efs.availability_zone_name
}

output "efs_access_arn" {
    value = aws_efs_access_point.efs-access-point.arn
}