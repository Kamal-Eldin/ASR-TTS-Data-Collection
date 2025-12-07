data "aws_ssm_parameter" "collector-db-pass" {
    name= "MYSQL_PASSWORD"
    region = var.region
    with_decryption= true
}

data "aws_ssm_parameter" "collector-db-root-pass" {
    name= "MYSQL_ROOT_PASSWORD"
    region = var.region
    with_decryption= true
}

data "aws_ssm_parameter" "collector-hf-token" {
    name= "HUGGINGFACE_TOKEN"
    region = var.region
    with_decryption= true
}

data "aws_iam_policy_document" "lambda-role-trust-policy" { # gives the lambda service permission to assume the role
    version = "2012-10-17"
    statement {
        effect = "Allow"
        actions = ["sts:AssumeRole"]
        principals {
            type = "Service"
            identifiers = ["lambda.amazonaws.com"]
        }
    }
}

data "aws_iam_policy" "lambda-basic-exe-policy" {
    name = "AWSLambdaBasicExecutionRole"
    
}
data "aws_iam_policy" "lambda-ecr-access-policy" {
    name = "AmazonEC2ContainerRegistryReadOnly"
    
}

data "aws_iam_policy" "lambda-vpc-access-policy" {
    name = "AWSLambdaVPCAccessExecutionRole"
}

data "aws_iam_policy" "lambda-efs-access" {
    name= "AmazonElasticFileSystemClientReadWriteAccess"
}

# data "aws_iam_policy_document" "net-interface-policy-doc" {
#     statement {
#         effect = "Allow"
#         actions = [
#             "ec2:DetachNetworkInterface",
#             "ec2:DeleteTags",
#             "ec2:DescribeTags",
#             "ec2:CreateTags",
#             "ec2:ResetNetworkInterfaceAttribute",
#             "ec2:ModifyNetworkInterfaceAttribute",
#             "ec2:DeleteNetworkInterface",
#             "ec2:CreateNetworkInterface",
#             "ec2:DeleteNetworkInterfacePermission",
#             "ec2:DescribeNetworkInterfaces",
#             "ec2:CreateNetworkInterfacePermission",
#             "ec2:DescribeNetworkInterfaceAttribute",
#             "ec2:AttachNetworkInterface",
#             "ec2:DescribeNetworkInterfacePermissions"
#             # "ec2:DescribeSubnets",
#             # "ec2:AssignPrivateIpAddresses",
#             # "ec2:UnassignPrivateIpAddresses"
#         ]
#         resources = [ "*" ]
#     }
# }