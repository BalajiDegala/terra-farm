# 03 — Random values and generated configuration

[Previous](02-storage-database.md) · [Index](../README.md) · [Next](04-messaging.md)

**Goal:** use multiple providers and generate configuration from real Terraform references.
**Prerequisite:** Chapter 02 passed.

## 1. Prepare this chapter

Start at the repository root. If still inside `lab/`, first run `cd ..`.

```text
python scripts/chapter.py 3
cd lab
```

Inspect the [new/replaced reference files](../examples/03/). The copier preserves state and
personal tfvars, and backs up overwritten source under `.workshop/backups/`.

`versions.tf` adds Random and Local. `random_id.app` creates a stable application identifier,
stored in state, rather than a different value on every plan. `local_file.app_config` writes
`generated/app-config.json`. Inspect its filename and template inputs before applying.

The template's `jsonencode(config)` escapes JSON correctly; `templatefile()` evaluates it with a map.
The bucket/table values come from resources, so Terraform infers their dependencies automatically.
Do not edit generated JSON as the source of truth; edit its Terraform/template inputs instead.
This chapter keeps existing bucket names stable rather than replacing buckets to add randomness.

## 2. Review the plan and apply

```text
terraform init
terraform fmt -recursive
terraform validate
terraform plan "-out=build/chapter03.tfplan"
terraform show build/chapter03.tfplan
```

Expect **2 additions**: one random ID and one local file. There should be no bucket replacements.
After applying, compare the generated table/bucket names with Terraform outputs and the AWS CLI.

Only after those changes match your expectations:

```text
terraform apply build/chapter03.tfplan
terraform state list
terraform output
```

## 3. Verify and finish

```text
terraform state show random_id.app
python -m json.tool generated/app-config.json
python ../scripts/aws_local.py dynamodb list-tables
terraform plan
```

The final plan should report no changes. A saved plan is a snapshot: after editing configuration,
discard the old plan and generate a new one before applying.

**Checkpoint:** The application ID stays stable, generated JSON contains resource-derived values, and the final plan is clean.

**Exercise:** Run two plans and verify the application ID stays the same. Explain which stored information
keeps it stable. Predict what deleting state would do, without actually deleting it.

**Troubleshooting:** If Terraform says a provider is missing, rerun `terraform init`. The Local provider writes files
on the machine running Terraform; it does not upload files into Floci.
