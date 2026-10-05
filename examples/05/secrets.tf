variable "demo_secret_note" {
  description = "Fake development data only; sensitive hides display, not state storage."
  type        = string
  default     = "local-learning-only"
  sensitive   = true
}

resource "random_password" "development" {
  length  = 24
  special = false
}

resource "aws_kms_key" "app" {
  description             = "Local lab application key"
  deletion_window_in_days = 7
}

resource "aws_kms_alias" "app" {
  name          = "alias/${local.name_prefix}"
  target_key_id = aws_kms_key.app.key_id
}

resource "aws_secretsmanager_secret" "app" {
  name                    = "${local.name_prefix}-app"
  kms_key_id              = aws_kms_key.app.arn
  recovery_window_in_days = 0 # Immediate removal of this fake local secret on destroy.
}

resource "aws_secretsmanager_secret_version" "app" {
  secret_id = aws_secretsmanager_secret.app.id
  secret_string = jsonencode({
    app_id   = random_id.app.hex
    password = random_password.development.result
    note     = var.demo_secret_note
  })
}

output "secret_arn" { value = aws_secretsmanager_secret.app.arn }
output "kms_key_id" { value = aws_kms_key.app.key_id }
