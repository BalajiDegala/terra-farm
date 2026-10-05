resource "aws_iam_role" "lambda" {
  name = "${local.name_prefix}-lambda"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_policy" "lambda" {
  name = "${local.name_prefix}-lambda"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["dynamodb:GetItem", "dynamodb:PutItem", "dynamodb:UpdateItem"]
        Resource = [aws_dynamodb_table.orders.arn, aws_dynamodb_table.products.arn]
      },
      {
        Effect   = "Allow"
        Action   = ["sqs:SendMessage", "sqs:ReceiveMessage", "sqs:DeleteMessage", "sqs:GetQueueAttributes"]
        Resource = aws_sqs_queue.orders.arn
      },
      {
        Effect   = "Allow"
        Action   = ["sns:Publish"]
        Resource = concat([aws_sns_topic.order_events.arn], aws_sns_topic.order_failures[*].arn)
      },
      {
        Effect   = "Allow"
        Action   = ["s3:PutObject"]
        Resource = "${local.archive_bucket_arn}/*"
      },
      {
        Effect   = "Allow"
        Action   = ["logs:CreateLogStream", "logs:PutLogEvents"]
        Resource = "arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.local.account_id}:log-group:/aws/lambda/${local.name_prefix}-*:log-stream:*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda" {
  role       = aws_iam_role.lambda.name
  policy_arn = aws_iam_policy.lambda.arn
}

output "lambda_role_name" { value = aws_iam_role.lambda.name }
