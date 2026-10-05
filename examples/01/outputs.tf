output "name_prefix" {
  description = "Normalized prefix that later resources will reference."
  value       = local.name_prefix
}

output "common_tags" {
  description = "Merged default tags for resources that support tagging."
  value       = local.common_tags
}

output "floci_endpoint" {
  description = "Local API endpoint selected for this lab."
  value       = var.floci_endpoint
}

output "aws_region" {
  description = "Region namespace selected for the local lab."
  value       = var.aws_region
}

output "local_account_id" {
  description = "Account ID read from Floci using the AWS provider's STS client."
  value       = data.aws_caller_identity.local.account_id
}
