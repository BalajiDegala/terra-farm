"""Small cross-platform workload/exercise helper. Run from lab/; read runbooks first."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
import urllib.request
import uuid

import aws_local

ROOT = Path(__file__).resolve().parents[1]


def aws(*arguments):
    output = aws_local.run(list(arguments), capture=True).stdout
    return json.loads(output) if output.strip() else {}


def outputs():
    executable = "terraform.exe" if os.name == "nt" else "terraform"
    binary = ROOT / ".tools" / "terraform" / executable
    terraform = str(binary) if binary.exists() else shutil.which("terraform")
    if not terraform:
        raise RuntimeError("Install Terraform and add it to PATH first.")
    result = subprocess.run([terraform, "output", "-json"], capture_output=True, text=True,
                            encoding="utf-8", check=True)
    values = {key: value["value"] for key, value in json.loads(result.stdout).items()}
    if values.get("floci_endpoint") not in {"http://localhost:4566", "http://127.0.0.1:4566"}:
        raise RuntimeError("Run from lab/ after applying the foundation chapter.")
    if values.get("aws_region") != "us-east-1":
        raise RuntimeError("These workload exercises use us-east-1; restore that region before running them.")
    return values


def seed(config):
    aws("dynamodb", "put-item", "--table-name", config["products_table"], "--item",
        json.dumps({"product_id": {"S": "coffee"}, "name": {"S": "Learning blend"}, "price_cents": {"N": "1200"}}))
    print("Seeded product coffee at 1200 cents.")


def smoke(config, use_api):
    seed(config)
    order = {"product_id": "coffee", "quantity": 2}
    if use_api:
        endpoint = config["api_endpoint"]
        if not endpoint.startswith(config["floci_endpoint"] + "/restapis/"):
            raise RuntimeError("Unexpected API URL; refusing to send a request.")
        request = urllib.request.Request(endpoint, data=json.dumps(order).encode(),
                                         headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(request, timeout=60) as response:
            if response.status != 202:
                raise RuntimeError(f"Expected HTTP 202; received {response.status}")
            accepted = json.load(response)
    else:
        result_file = Path("generated/invoke-result.json")
        result = aws("lambda", "invoke", "--function-name", config["create_order_function"],
                     "--cli-binary-format", "raw-in-base64-out", "--payload", json.dumps(order), str(result_file))
        if "FunctionError" in result:
            raise RuntimeError(result_file.read_text())
        response = json.loads(result_file.read_text())
        if response["statusCode"] != 202:
            raise RuntimeError(response)
        accepted = json.loads(response["body"])
    order_id = accepted["order_id"]
    deadline = time.monotonic() + 90
    while time.monotonic() < deadline:
        item = aws("dynamodb", "get-item", "--table-name", config["orders_table"],
                   "--key", json.dumps({"order_id": {"S": order_id}}), "--consistent-read").get("Item", {})
        if item.get("status", {}).get("S") == "PROCESSED":
            break
        time.sleep(2)
    else:
        raise RuntimeError(f"Order {order_id} did not reach PROCESSED. Inspect Lambda logs and the DLQ.")
    aws("s3api", "head-object", "--bucket", config["archive_bucket"], "--key", f"orders/{order_id}.json")
    # Consume only this test's notification; leave unrelated messages for their owners.
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        messages = aws("sqs", "receive-message", "--queue-url", config["notification_queue_url"],
                       "--max-number-of-messages", "10", "--wait-time-seconds", "2").get("Messages", [])
        for message in messages:
            if json.loads(message["Body"]).get("order_id") == order_id:
                aws("sqs", "delete-message", "--queue-url", config["notification_queue_url"],
                    "--receipt-handle", message["ReceiptHandle"])
                print(f"PASS: {order_id}: accepted -> queued -> PROCESSED -> archived -> notified")
                return
    raise RuntimeError(f"Order processed but its SNS-to-SQS notification was not found: {order_id}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["seed", "smoke-lambda", "smoke-api", "publish", "event", "drift", "import-create"])
    args = parser.parse_args()
    config = outputs()
    if args.action == "seed":
        seed(config)
    elif args.action.startswith("smoke-"):
        smoke(config, args.action == "smoke-api")
    elif args.action == "publish":
        print(aws("sns", "publish", "--topic-arn", config["order_events_topic_arn"],
                  "--message", json.dumps({"lesson": "messaging", "message": "hello"})))
        print(aws("sqs", "receive-message", "--queue-url", config["notification_queue_url"], "--wait-time-seconds", "5"))
    elif args.action == "event":
        marker = str(uuid.uuid4())
        result = aws("events", "put-events", "--entries", json.dumps([{
            "EventBusName": config["event_bus_name"], "Source": "shop.audit",
            "DetailType": "WorkshopAudit", "Detail": json.dumps({"lesson": "events", "marker": marker})}]))
        if result.get("FailedEntryCount"):
            raise RuntimeError(result)
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            for message in aws("sqs", "receive-message", "--queue-url", config["notification_queue_url"],
                               "--max-number-of-messages", "10", "--wait-time-seconds", "2").get("Messages", []):
                if json.loads(message["Body"]).get("detail", {}).get("marker") == marker:
                    aws("sqs", "delete-message", "--queue-url", config["notification_queue_url"],
                        "--receipt-handle", message["ReceiptHandle"])
                    print("PASS: EventBridge audit event arrived in the notification queue.")
                    return
        raise RuntimeError("Event accepted but matching queue delivery was not observed.")
    elif args.action == "drift":
        print(aws("sqs", "set-queue-attributes", "--queue-url", config["orders_queue_url"],
                  "--attributes", "VisibilityTimeout=60"))
        print("Changed orders queue timeout to 60 outside Terraform. Run terraform plan; desired value is 180.")
    elif args.action == "import-create":
        name = f"/{config['name_prefix']}/imported-note"
        print(aws("ssm", "put-parameter", "--name", name, "--type", "String", "--value", "created-outside-terraform"))
        print(f"Import ID: {name}")


if __name__ == "__main__":
    main()
