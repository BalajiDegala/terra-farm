locals {
  normalized_project_name = lower(replace(var.project_name, "_", "-"))
  name_prefix             = format("%s-%s", local.normalized_project_name, var.environment)

  common_tags = merge(
    var.common_tags,
    {
      Project     = local.normalized_project_name
      Environment = var.environment
      ManagedBy   = "Terraform"
    },
  )
}
