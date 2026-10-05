resource "aws_api_gateway_rest_api" "orders" {
  name = "${local.name_prefix}-api"
  body = jsonencode({
    openapi = "3.0.1"
    info    = { title = "Local orders API", version = "1.0" }
    paths = {
      "/orders" = {
        post = {
          responses = { "202" = { description = "Order accepted" } }
          "x-amazon-apigateway-integration" = {
            type       = "aws_proxy"
            httpMethod = "POST"
            uri        = aws_lambda_function.app["create_order"].invoke_arn
          }
        }
      }
    }
  })
}

resource "aws_lambda_permission" "api" {
  statement_id  = "AllowLocalApi"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.app["create_order"].function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.orders.execution_arn}/*/POST/orders"
}

resource "aws_api_gateway_deployment" "orders" {
  rest_api_id = aws_api_gateway_rest_api.orders.id
  triggers    = { redeployment = sha1(aws_api_gateway_rest_api.orders.body) }
  lifecycle {
    create_before_destroy = true
  }
  depends_on = [aws_lambda_permission.api]
}

resource "aws_api_gateway_stage" "orders" {
  provider      = aws.untagged
  rest_api_id   = aws_api_gateway_rest_api.orders.id
  deployment_id = aws_api_gateway_deployment.orders.id
  stage_name    = var.environment
}

output "api_endpoint" {
  value = "${var.floci_endpoint}/restapis/${aws_api_gateway_rest_api.orders.id}/${aws_api_gateway_stage.orders.stage_name}/_user_request_/orders"
}
