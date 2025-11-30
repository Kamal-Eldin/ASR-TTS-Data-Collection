

resource "aws_efs_file_system" "data-app-efs" {
    encrypted = true
    region = var.region
    availability_zone_name = "${var.region}a" # equivalent to subnet-1
    performance_mode = "generalPurpose"

    tags = {
      "project"             = "${var.project_name}"
      "service"             = "${var.application_name}-EFS"
      "function"            = "provide elastic file system to the lambda backend"
    }

}

resource "aws_efs_access_point" "efs-access-point" {
    region = var.region
    file_system_id = aws_efs_file_system.data-app-efs.id
    posix_user {
      uid = 1000
      gid = 1000
    }
    root_directory {
      path = "/lambda"
      creation_info {
        owner_gid   = 1000 
        owner_uid   = 1000
        permissions = "755" #chmod_directory: user(read/write/execute: 7), group(read/execute 5), others(read/execute 5)
      }
    }

}

resource "aws_efs_mount_target" "lambda-efs-mount" {
    count = 1
    region = var.region
    file_system_id = aws_efs_file_system.data-app-efs.id
    subnet_id = var.subnets_ids[0]   # subnet-1 -> associated with {region}a # public subnet
    security_groups = [ var.efs-secgrp_id ]

  
}