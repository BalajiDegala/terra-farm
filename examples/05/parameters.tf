locals {
  parameters = {
    environment         = var.environment
    "orders/table-name" = aws_dynamodb_table.orders.name
    "orders/queue-name" = aws_sqs_queue.orders.name
  }
}

resource "aws_ssm_parameter" "app" {
  for_each = local.parameters
  name     = "/${local.name_prefix}/${each.key}"
  type     = "String"
  value    = each.value
}
