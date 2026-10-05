resource "random_id" "app" {
  byte_length = 4
}

resource "local_file" "app_config" {
  filename = "${path.module}/generated/app-config.json"
  content = templatefile("${path.module}/templates/app-config.json.tftpl", {
    config = {
      app_id              = random_id.app.hex
      environment         = var.environment
      endpoint            = var.floci_endpoint
      region              = var.aws_region
      orders_table        = aws_dynamodb_table.orders.name
      products_table      = aws_dynamodb_table.products.name
      assets_bucket       = local.assets_bucket_name
      archive_bucket      = local.archive_bucket_name
      orders_queue        = aws_sqs_queue.orders.url
      notifications_queue = aws_sqs_queue.notifications.url
      order_events_topic  = aws_sns_topic.order_events.arn
    }
  })
}

output "app_config_path" { value = local_file.app_config.filename }
