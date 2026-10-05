resource "aws_s3_bucket" "assets" {
  bucket        = "${local.name_prefix}-assets"
  force_destroy = true # Local lab only: cleanup also removes test objects.
}

resource "aws_s3_bucket" "order_archive" {
  bucket        = "${local.name_prefix}-archive"
  force_destroy = true
}

# Later lessons use these references, making the module refactor small.
locals {
  assets_bucket_name  = aws_s3_bucket.assets.id
  archive_bucket_name = aws_s3_bucket.order_archive.id
  archive_bucket_arn  = aws_s3_bucket.order_archive.arn
}

output "assets_bucket" { value = local.assets_bucket_name }
output "archive_bucket" { value = local.archive_bucket_name }
