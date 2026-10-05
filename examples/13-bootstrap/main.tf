terraform {
  required_version = ">= 1.10.0, < 2.0.0"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 6.0" }
  }
}

provider "aws" {
  region                      = "us-east-1"
  access_key                  = "test"
  secret_key                  = "test"
  token                       = "test"
  profile                     = "default"
  shared_config_files         = ["${path.module}/../config/aws-local.ini"]
  shared_credentials_files    = ["${path.module}/../config/aws-local.ini"]
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true
  s3_use_path_style           = true
  endpoints {
    s3  = "http://localhost:4566"
    sts = "http://localhost:4566"
  }
}

resource "aws_s3_bucket" "state" {
  bucket        = "terraform-workshop-state"
  force_destroy = true # Only destroy AFTER migrating application state back to local.
}

resource "aws_s3_bucket_versioning" "state" {
  bucket = aws_s3_bucket.state.id
  versioning_configuration { status = "Enabled" }
}
