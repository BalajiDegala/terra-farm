module "storage" {
  source      = "./modules/storage"
  name_prefix = local.name_prefix
}

moved {
  from = aws_s3_bucket.assets
  to   = module.storage.aws_s3_bucket.assets
}

moved {
  from = aws_s3_bucket.order_archive
  to   = module.storage.aws_s3_bucket.order_archive
}

locals {
  assets_bucket_name  = module.storage.assets_bucket_name
  archive_bucket_name = module.storage.archive_bucket_name
  archive_bucket_arn  = module.storage.archive_bucket_arn
}

output "assets_bucket" { value = local.assets_bucket_name }
output "archive_bucket" { value = local.archive_bucket_name }
