# 02 — Storage and database

[Previous](01-foundation.md) · [Index](../README.md) · [Next](03-random-local.md)

**Goal:** create the first four managed resources. **Prerequisite:** Chapter 01 has been applied.
S3 stores assets and order archives; DynamoDB stores orders and products.

## 1. Prepare this chapter

Start at the repository root. If still inside `lab/`, first run `cd ..`.

```text
python scripts/chapter.py 2
cd lab
```

Inspect the [new/replaced reference files](../examples/02/). The copier preserves state and
personal tfvars, and backs up overwritten source under `.workshop/backups/`.

In `storage.tf`, `resource "aws_s3_bucket" "assets"` declares a managed object:

- `resource` is the block kind; `aws_s3_bucket` is the provider's resource type.
- `assets` is Terraform's local label, not the bucket's cloud name.
- `bucket` sets that name; `${local.name_prefix}-assets` combines a reference with text.
- The resource address is `aws_s3_bucket.assets`; `.id` reads its provider-assigned identifier.

`force_destroy = true` permits deletion of this lab's test objects during cleanup. It belongs only in
this disposable lab. Both tables use on-demand billing syntax for realism; Floci creates no AWS bill.
`hash_key` identifies the partition key. `attribute` declares key types, not every item field.
The three storage locals form references that we will redirect through a module in Chapter 12.

## 2. Review the plan and apply

```text
terraform init
terraform fmt -recursive
terraform validate
terraform plan "-out=build/chapter02.tfplan"
terraform show build/chapter02.tfplan
```

Expect **4 to add, 0 to change, 0 to destroy**: two buckets and two tables.
`+` means create; `(known after apply)` means the provider will supply a value during creation.
After apply, check for `terraform-lab-dev-assets`, `terraform-lab-dev-archive`, and the two table names.

Only after those changes match your expectations:

```text
terraform apply build/chapter02.tfplan
terraform state list
terraform output
```

## 3. Verify and finish

```text
python ../scripts/aws_local.py s3api list-buckets
python ../scripts/aws_local.py dynamodb list-tables
terraform state show aws_s3_bucket.assets
terraform state show aws_dynamodb_table.orders
terraform plan
```

The final plan should report no changes. A saved plan is a snapshot: after editing configuration,
discard the old plan and generate a new one before applying.

**Checkpoint:** Two buckets and two tables exist, state shows all four resources, and the final plan is clean.

**Exercise:** Find the DynamoDB key in `terraform state show aws_dynamodb_table.products`. Explain why
the table can later contain a `price_cents` field without adding an `attribute` block here.

**Troubleshooting:** An already-existing bucket usually means a different state owns the name. Find that state;
do not delete its resources or discard state to make the error disappear.
