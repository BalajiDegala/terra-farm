# 04 — Queues and notifications

[Previous](03-random-local.md) · [Index](../README.md) · [Next](05-configuration-secrets.md)

**Goal:** wire asynchronous order processing and notifications. **Prerequisite:** Chapter 03 passed.

## 1. Prepare this chapter

Start at the repository root. If still inside `lab/`, first run `cd ..`.

```text
python scripts/chapter.py 4
cd lab
```

Inspect the [new/replaced reference files](../examples/04/). The copier preserves state and
personal tfvars, and backs up overwritten source under `.workshop/backups/`.

`messaging.tf` adds three SQS queues, two SNS topics, a queue policy, and a subscription.
`providers.tf` adds the SQS and SNS local endpoints. `generated.tf` includes messaging identifiers.
The orders queue's redrive policy sends repeatedly failed messages to the DLQ after three receives.
Queue **URLs** are used in SQS requests; **ARNs** identify resources in policies and subscriptions.

`jsonencode()` builds policy JSON. The DLQ ARN reference makes its queue an implicit prerequisite.
The subscription's `depends_on` ensures queue permission exists; its topic/queue references alone
do not express that policy dependency. Avoid adding blanket `depends_on` to every resource.

The optional failure topic uses `count = var.enable_failure_topic ? 1 : 0`; its address ends in `[0]`.
`try(..., null)` handles the output when it is disabled. Keep the default enabled for this course.

## 2. Review the plan and apply

```text
terraform init
terraform fmt -recursive
terraform validate
terraform plan "-out=build/chapter04.tfplan"
terraform show build/chapter04.tfplan
```

Expect **7 additions** and regeneration of the local configuration file (Local may report that
as a replacement). Existing AWS storage/database resources should remain intact.
The publish helper sends a test SNS message and receives it from the notification queue;
verify the returned body contains `lesson: messaging`.

Only after those changes match your expectations:

```text
terraform apply build/chapter04.tfplan
terraform state list
terraform output
```

## 3. Verify and finish

```text
python ../scripts/aws_local.py sqs list-queues
python ../scripts/aws_local.py sns list-topics
python ../scripts/aws_local.py sns list-subscriptions
python ../scripts/lab.py publish
terraform state show aws_sqs_queue.orders
terraform plan
```

The final plan should report no changes. A saved plan is a snapshot: after editing configuration,
discard the old plan and generate a new one before applying.

**Checkpoint:** The test SNS message is visible in the notification queue, and the final plan is clean.

**Exercise:** Run `terraform plan "-var=enable_failure_topic=false"` and identify the indexed topic scheduled
for removal. Do not apply it; return to the default plan. Why are named `for_each` keys often clearer?

**Troubleshooting:** An empty receive response may mean another receive has temporarily hidden the message.
Wait for its visibility timeout or publish a new message. Inspect the subscription and queue policy.
