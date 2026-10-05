variable "enable_failure_topic" {
  description = "Create the optional local failure topic. count demonstrates an on/off resource."
  type        = bool
  default     = true
}

resource "aws_sqs_queue" "dead_letter" {
  name = "${local.name_prefix}-dead-letter"
}

resource "aws_sqs_queue" "orders" {
  name                       = "${local.name_prefix}-orders"
  visibility_timeout_seconds = 180
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dead_letter.arn
    maxReceiveCount     = 3
  })
}

resource "aws_sqs_queue" "notifications" {
  name = "${local.name_prefix}-notifications"
}

resource "aws_sns_topic" "order_events" {
  name = "${local.name_prefix}-order-events"
}

resource "aws_sns_topic" "order_failures" {
  count = var.enable_failure_topic ? 1 : 0
  name  = "${local.name_prefix}-order-failures"
}

resource "aws_sqs_queue_policy" "notifications" {
  queue_url = aws_sqs_queue.notifications.url
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "sns.amazonaws.com" }
      Action    = "sqs:SendMessage"
      Resource  = aws_sqs_queue.notifications.arn
      Condition = { ArnEquals = { "aws:SourceArn" = aws_sns_topic.order_events.arn } }
      }, {
      Effect    = "Allow"
      Principal = { Service = "events.amazonaws.com" }
      Action    = "sqs:SendMessage"
      Resource  = aws_sqs_queue.notifications.arn
      Condition = { ArnEquals = { "aws:SourceArn" = aws_cloudwatch_event_rule.audit.arn } }
    }]
  })
}

resource "aws_sns_topic_subscription" "notifications" {
  topic_arn            = aws_sns_topic.order_events.arn
  protocol             = "sqs"
  endpoint             = aws_sqs_queue.notifications.arn
  raw_message_delivery = true
  depends_on           = [aws_sqs_queue_policy.notifications]
}

output "orders_queue_url" { value = aws_sqs_queue.orders.url }
output "notification_queue_url" { value = aws_sqs_queue.notifications.url }
output "dead_letter_queue_url" { value = aws_sqs_queue.dead_letter.url }
output "order_events_topic_arn" { value = aws_sns_topic.order_events.arn }
output "order_failures_topic_arn" { value = try(aws_sns_topic.order_failures[0].arn, null) }
