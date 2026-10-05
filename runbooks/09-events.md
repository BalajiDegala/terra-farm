# 09 — EventBridge audit events

[Previous](08-api.md) · [Index](../README.md) · [Next](10-expressions.md)

**Goal:** add an independent audit-event path. **Prerequisite:** Chapter 08 passed.
The main order workflow still publishes SNS directly; this lesson publishes an audit event through the CLI.

## 1. Prepare this chapter

Start at the repository root. If still inside `lab/`, first run `cd ..`.

```text
python scripts/chapter.py 9
cd lab
```

Inspect the [new/replaced reference files](../examples/09/). The copier preserves state and
personal tfvars, and backs up overwritten source under `.workshop/backups/`.

`events.tf` adds a custom bus, a rule matching `source = shop.audit`, and an SQS target.
`messaging.tf` replaces the existing notification queue policy with one that allows both the SNS topic
and this EventBridge rule. There is one Terraform owner for the queue policy, avoiding competing policies.
The new permission narrows delivery to the rule's source ARN. The event target depends on that permission.
`providers.tf` maps the AWS provider's `cloudwatchevents` endpoint name to local Floci.

## 2. Review the plan and apply

```text
terraform init
terraform fmt -recursive
terraform validate
terraform plan "-out=build/chapter09.tfplan"
terraform show build/chapter09.tfplan
```

Expect **3 additions** and an in-place update to the notification queue policy.
The event helper publishes a unique marker and checks delivery of that exact event into SQS.
An accepted `PutEvents` response by itself does not prove the rule and target delivered anything.
With default choices, there are now **36 managed resources**, plus data sources.

Only after those changes match your expectations:

```text
terraform apply build/chapter09.tfplan
terraform state list
terraform output
```

## 3. Verify and finish

```text
python ../scripts/aws_local.py events list-event-buses
python ../scripts/aws_local.py events list-rules --event-bus-name terraform-lab-dev-orders
python ../scripts/lab.py event
terraform plan
```

The final plan should report no changes. A saved plan is a snapshot: after editing configuration,
discard the old plan and generate a new one before applying.

**Checkpoint:** The matching audit event reaches SQS, 36 managed resources are present, and the final plan is clean.

**Exercise:** Read the helper's event payload and the rule pattern. Predict what changing Source to
`shop.other` would do: the API can accept an event without matching this rule. Do not edit the shared policy
outside Terraform during this chapter.

**Troubleshooting:** For accepted-but-undelivered events, check Source, bus name, rule, target ARN, and the queue policy.
Use `terraform output -raw event_bus_name` if you customized resource names.
