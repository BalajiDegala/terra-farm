resource "aws_cloudwatch_event_bus" "orders" {
  name = "${local.name_prefix}-orders"
}

resource "aws_cloudwatch_event_rule" "audit" {
  name           = "${local.name_prefix}-audit"
  event_bus_name = aws_cloudwatch_event_bus.orders.name
  event_pattern  = jsonencode({ source = ["shop.audit"] })
}

resource "aws_cloudwatch_event_target" "notifications" {
  rule           = aws_cloudwatch_event_rule.audit.name
  event_bus_name = aws_cloudwatch_event_bus.orders.name
  target_id      = "notifications"
  arn            = aws_sqs_queue.notifications.arn
  depends_on     = [aws_sqs_queue_policy.notifications]
}

output "event_bus_name" { value = aws_cloudwatch_event_bus.orders.name }
