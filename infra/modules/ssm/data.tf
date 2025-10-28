locals {
    workspace-dir= dirname(abspath(path.root))
    secrets-path= "${dirname(abspath(path.root))}/secrets"
}


data "local_sensitive_file" "db-pass" {
    filename = "${local.secrets-path}/db_password.txt"
}

data "local_sensitive_file" "db-root-pass" {
    filename = "${local.secrets-path}/db_root_password.txt"
}


data "local_sensitive_file" "hf-token" {
    filename = "${local.secrets-path}/hf_token.txt"
}