# Floci 2.1.0 does not round-trip Lambda event-source mapping tags with AWS 6.67.0.
# Use a local alias without default_tags for that resource instead of hiding drift.
provider "aws" {
  alias                       = "untagged"
  region                      = var.aws_region
  access_key                  = "test"
  secret_key                  = "test"
  token                       = "test"
  profile                     = "default"
  shared_config_files         = ["${path.module}/config/aws-local.ini"]
  shared_credentials_files    = ["${path.module}/config/aws-local.ini"]
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true
  max_retries                 = 1
  endpoints {
    lambda = var.floci_endpoint
    sts    = var.floci_endpoint
  }
}
