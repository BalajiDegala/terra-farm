provider "aws" {
  region = var.aws_region

  # Deliberately fake Floci credentials, including the session token.
  access_key = "test"
  secret_key = "test"
  token      = "test"

  # Keep personal AWS profiles out of this lab even without Use-LocalLab.ps1.
  profile                  = "default"
  shared_config_files      = ["${path.module}/config/aws-local.ini"]
  shared_credentials_files = ["${path.module}/config/aws-local.ini"]

  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true
  s3_use_path_style           = true
  max_retries                 = 1

  # Add each service endpoint only after checking its Floci compatibility.
  endpoints {
    sts      = var.floci_endpoint
    s3       = var.floci_endpoint
    dynamodb = var.floci_endpoint
    sns      = var.floci_endpoint
    sqs      = var.floci_endpoint
  }

  default_tags {
    tags = local.common_tags
  }
}

# A data source reads existing information; it creates no AWS resource.
# This lookup proves the provider can communicate with Floci's STS endpoint.
data "aws_caller_identity" "local" {
  lifecycle {
    postcondition {
      condition     = self.account_id == "000000000000"
      error_message = "Expected the default Floci account 000000000000. Check the running emulator configuration."
    }
  }
}
