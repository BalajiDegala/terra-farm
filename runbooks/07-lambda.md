# 07 — Python Lambdas and the order workflow

[Previous](06-iam.md) · [Index](../README.md) · [Next](08-api.md)

**Goal:** run an order through two real local Python functions. **Prerequisite:** Chapter 06 passed.

Before preparing the chapter, enable Docker-backed Lambda execution from the repository root:

```text
docker compose -f compose.yaml -f compose.lambda.yaml up -d --wait floci
docker pull public.ecr.aws/lambda/python:3.12
```

This override mounts the Docker socket and runs Floci as root so it can launch runtime containers.
Socket access grants control of the local Docker daemon; use this on your development machine.
It works with the reference Docker Desktop/Linux Engine setup, without exposing additional host ports.
Use the same two `-f` files when starting/resuming the lab from this chapter onward.
The explicit pull downloads the Python runtime before the first invocation, avoiding a smoke-test
timeout while the image downloads. Docker selects the image for your machine's architecture.

## 1. Prepare this chapter

Start at the repository root. If still inside `lab/`, first run `cd ..`.

```text
python scripts/chapter.py 7
cd lab
```

Inspect the [new/replaced reference files](../examples/07/). The copier preserves state and
personal tfvars, and backs up overwritten source under `.workshop/backups/`.

`versions.tf` adds Archive; `data.archive_file.lambda` packages each handler directory into a ZIP.
It is a data source: it calculates an archive rather than creating a cloud resource.
`source_code_hash` makes code changes trigger Lambda updates. `for_each` gives the two functions
stable keys `create_order` and `process_order`, reused for archives and log groups.
`compatibility-provider.tf` defines the `aws.untagged` provider alias, with the same fake credentials
and local endpoints but no default tags. The pinned Floci/provider combination does not return
event-source mapping tags consistently, causing perpetual drift with default tags. Only the mapping
selects this alias; other resources keep their tags. This is a documented emulator compatibility choice,
not an `ignore_changes` rule that suppresses differences.
The conditional retention setting is 7 days in dev/test and 30 for the local prod label.

Read both `handler.py` files. Create-order validates JSON, reads the product price, writes PENDING
to DynamoDB, and sends SQS a work message. Process-order writes an S3 archive, publishes SNS, and
updates the order to PROCESSED. The event-source mapping polls SQS; partial batch failures allow retries.
The queue's visibility timeout is longer than the function timeout, reducing overlapping retries.

Inside a Lambda container, `localhost` means that container. SDK requests therefore use
`http://floci:4566`, and the handler rewrites the host portion of the returned queue URL.
On the host, Terraform and CLI still use localhost. All handler clients explicitly use the local endpoint.

The role ARN reference orders function creation after the role; explicit `depends_on` adds the
policy attachment and log groups because Terraform cannot infer those relationships from the ARN alone.

## 2. Review the plan and apply

```text
terraform init
terraform fmt -recursive
terraform validate
terraform plan "-out=build/chapter07.tfplan"
terraform show build/chapter07.tfplan
```

Expect **5 additions**: two functions, two log groups, one queue-to-Lambda mapping.
The smoke helper seeds a `coffee` product, invokes create-order, waits for PROCESSED, checks the
archive object, and consumes the matching notification. Expect a `PASS` line covering all stages.
This is an end-to-end check, not merely evidence that `CreateFunction` succeeded.

Only after those changes match your expectations:

```text
terraform apply build/chapter07.tfplan
terraform state list
terraform output
```

## 3. Verify and finish

```text
python ../scripts/aws_local.py lambda list-functions
python ../scripts/aws_local.py lambda list-event-source-mappings
python ../scripts/aws_local.py logs describe-log-groups
python ../scripts/lab.py smoke-lambda
terraform plan
```

The final plan should report no changes. A saved plan is a snapshot: after editing configuration,
discard the old plan and generate a new one before applying.

**Checkpoint:** The smoke check reports accepted, queued, processed, archived, and notified; the final plan is clean.

**Exercise:** Change a harmless log message in process-order, then plan. Find the changed code hash and
in-place Lambda update. Apply the reviewed change, run smoke again, then restore the source and apply.
Explain why retries can duplicate SNS notifications and why this sample is not an exactly-once system.

**Troubleshooting:** If Lambda creation succeeds but invocation fails, inspect `docker compose logs --tail 100 floci`,
runtime image downloads, and socket access. Check CloudWatch with the AWS wrapper and do not
switch endpoints to AWS. See the networking and cold-start entries in troubleshooting.
