"""Small local teaching workload; DynamoDB and SQS writes are not transactional."""
import base64
import json
import os
import uuid
from urllib.parse import urlsplit, urlunsplit

import boto3


def client(service):
    return boto3.client(service, endpoint_url=os.environ["FLOCI_ENDPOINT"],
                        region_name=os.environ["LAB_REGION"],
                        aws_access_key_id="test", aws_secret_access_key="test")


def response(status, body):
    return {"statusCode": status, "headers": {"Content-Type": "application/json"},
            "body": json.dumps(body)}


def handler(event, context):
    try:
        body = event.get("body", event)
        if event.get("isBase64Encoded"):
            body = base64.b64decode(body).decode("utf-8")
        order = json.loads(body) if isinstance(body, str) else body
        product = order.get("product_id")
        quantity = order.get("quantity")
        if not isinstance(product, str) or not product.strip():
            return response(400, {"error": "product_id must be a nonempty string"})
        if type(quantity) is not int or not 1 <= quantity <= 100:
            return response(400, {"error": "quantity must be an integer from 1 to 100"})
    except (ValueError, TypeError, AttributeError, UnicodeError):
        return response(400, {"error": "Expected a JSON object with product_id and quantity"})

    database = client("dynamodb")
    product_item = database.get_item(TableName=os.environ["PRODUCTS_TABLE"],
                                    Key={"product_id": {"S": product}}).get("Item")
    if not product_item:
        return response(404, {"error": "Product not found; run the seed step"})
    payload = {"order_id": str(uuid.uuid4()), "product_id": product, "quantity": quantity,
               "total_cents": int(product_item["price_cents"]["N"]) * quantity}
    database.put_item(TableName=os.environ["ORDERS_TABLE"], Item={
        "order_id": {"S": payload["order_id"]}, "product_id": {"S": product},
        "quantity": {"N": str(quantity)}, "total_cents": {"N": str(payload["total_cents"])},
        "status": {"S": "PENDING"}})
    # Queue URLs are returned for the host; Lambda must use the container hostname.
    queue = urlsplit(os.environ["ORDERS_QUEUE_URL"])
    endpoint = urlsplit(os.environ["FLOCI_ENDPOINT"])
    queue_url = urlunsplit((endpoint.scheme, endpoint.netloc, queue.path, queue.query, ""))
    client("sqs").send_message(QueueUrl=queue_url, MessageBody=json.dumps(payload))
    return response(202, payload)
