"""SQS is at-least-once: archive writes are repeatable; SNS notifications may duplicate."""
import json
import logging
import os

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def client(service):
    return boto3.client(service, endpoint_url=os.environ["FLOCI_ENDPOINT"],
                        region_name=os.environ["LAB_REGION"],
                        aws_access_key_id="test", aws_secret_access_key="test")


def handler(event, context):
    failures = []
    for record in event.get("Records", []):
        try:
            order = json.loads(record["body"])
            order_id = order["order_id"]
            order["status"] = "PROCESSED"
            client("s3").put_object(Bucket=os.environ["ARCHIVE_BUCKET"],
                                    Key=f"orders/{order_id}.json", Body=json.dumps(order),
                                    ContentType="application/json")
            client("sns").publish(TopicArn=os.environ["EVENTS_TOPIC_ARN"], Message=json.dumps(order))
            client("dynamodb").update_item(
                TableName=os.environ["ORDERS_TABLE"], Key={"order_id": {"S": order_id}},
                UpdateExpression="SET #status = :status",
                ExpressionAttributeNames={"#status": "status"},
                ExpressionAttributeValues={":status": {"S": "PROCESSED"}},
                ConditionExpression="attribute_exists(order_id)")
            logger.info("Processed order %s", order_id)
        except Exception:
            logger.exception("Processing failed for message %s", record["messageId"])
            failures.append({"itemIdentifier": record["messageId"]})
            if os.environ.get("FAILURES_TOPIC_ARN"):
                try:
                    client("sns").publish(TopicArn=os.environ["FAILURES_TOPIC_ARN"],
                                          Message=json.dumps({"message_id": record["messageId"], "status": "FAILED"}))
                except Exception:
                    logger.exception("Failure notification failed")
    return {"batchItemFailures": failures}
