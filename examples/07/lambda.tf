locals {
  lambda_names = {
    create_order  = "${local.name_prefix}-create-order"
    process_order = "${local.name_prefix}-process-order"
  }
  lambda_environment = {
    FLOCI_ENDPOINT     = "http://floci:4566"
    LAB_REGION         = var.aws_region
    ORDERS_TABLE       = aws_dynamodb_table.orders.name
    PRODUCTS_TABLE     = aws_dynamodb_table.products.name
    ORDERS_QUEUE_URL   = aws_sqs_queue.orders.url
    EVENTS_TOPIC_ARN   = aws_sns_topic.order_events.arn
    FAILURES_TOPIC_ARN = try(aws_sns_topic.order_failures[0].arn, "")
    ARCHIVE_BUCKET     = local.archive_bucket_name
  }
}

data "archive_file" "lambda" {
  for_each    = local.lambda_names
  type        = "zip"
  source_dir  = "${path.module}/lambda/${each.key}"
  output_path = "${path.module}/build/${each.key}.zip"
}

resource "aws_cloudwatch_log_group" "lambda" {
  for_each          = local.lambda_names
  name              = "/aws/lambda/${each.value}"
  retention_in_days = var.environment == "prod" ? 30 : 7
}

resource "aws_lambda_function" "app" {
  for_each         = local.lambda_names
  function_name    = each.value
  role             = aws_iam_role.lambda.arn
  runtime          = "python3.12"
  handler          = "handler.handler"
  filename         = data.archive_file.lambda[each.key].output_path
  source_code_hash = data.archive_file.lambda[each.key].output_base64sha256
  timeout          = 30
  memory_size      = 256
  environment {
    variables = local.lambda_environment
  }
  # The role reference cannot infer its policy attachment or pre-created log groups.
  depends_on = [aws_iam_role_policy_attachment.lambda, aws_cloudwatch_log_group.lambda]
}

resource "aws_lambda_event_source_mapping" "orders" {
  provider                = aws.untagged
  event_source_arn        = aws_sqs_queue.orders.arn
  function_name           = aws_lambda_function.app["process_order"].arn
  batch_size              = 1
  function_response_types = ["ReportBatchItemFailures"]
}

output "create_order_function" { value = aws_lambda_function.app["create_order"].function_name }
output "process_order_function" { value = aws_lambda_function.app["process_order"].function_name }
