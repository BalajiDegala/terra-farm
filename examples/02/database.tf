resource "aws_dynamodb_table" "orders" {
  name         = "${local.name_prefix}-orders"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "order_id"
  attribute {
    name = "order_id"
    type = "S"
  }
}

resource "aws_dynamodb_table" "products" {
  name         = "${local.name_prefix}-products"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "product_id"
  attribute {
    name = "product_id"
    type = "S"
  }
}

output "orders_table" { value = aws_dynamodb_table.orders.name }
output "products_table" { value = aws_dynamodb_table.products.name }
