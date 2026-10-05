terraform {
  required_providers {
    aws = { source = "hashicorp/aws" }
  }
}

variable "name_prefix" { type = string }

resource "aws_s3_bucket" "assets" {
  bucket        = "${var.name_prefix}-assets"
  force_destroy = true
}

resource "aws_s3_bucket" "order_archive" {
  bucket        = "${var.name_prefix}-archive"
  force_destroy = true
}

output "assets_bucket_name" { value = aws_s3_bucket.assets.id }
output "archive_bucket_name" { value = aws_s3_bucket.order_archive.id }
output "archive_bucket_arn" { value = aws_s3_bucket.order_archive.arn }
