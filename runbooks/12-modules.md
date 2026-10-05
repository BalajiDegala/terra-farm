# 12 — Refactor storage into a module

[Previous](11-state.md) · [Index](../README.md) · [Next](13-remote-state.md)

**Goal:** change Terraform organization without recreating buckets.
**Start:** Chapter 11 complete; state still contains `aws_s3_bucket.assets` and `aws_s3_bucket.order_archive`.

## 1. Prepare the refactor

From the repository root:

```text
python scripts/chapter.py 12
cd lab
terraform init
terraform fmt -recursive
terraform validate
terraform plan "-out=build/modules.tfplan"
terraform show build/modules.tfplan
```

Inspect [the reference changes](../examples/12/). `lab/` is the **root module**. The new
`modules/storage/` directory is a **child module** containing the two existing resources.
The module's `name_prefix` is an input; its outputs expose bucket names and the archive ARN.
`module.storage.archive_bucket_name` reads one of those outputs. The child inherits the configured
AWS provider, including local endpoints and tags; do not create an unconfigured AWS provider inside it.

`storage.tf` now calls that module and redirects the existing locals through its outputs, so IAM,
Lambda environment values, and generated configuration can keep their existing references.

## 2. Interpret the moves before applying

Expect these address changes:

```text
aws_s3_bucket.assets -> module.storage.aws_s3_bucket.assets
aws_s3_bucket.order_archive -> module.storage.aws_s3_bucket.order_archive
```

The `moved` blocks connect old state addresses to the new ones. The plan should report **0 to add,
0 to change, 0 to destroy**, apart from unrelated exercises you intentionally retained.
If it proposes deleting and recreating either bucket, stop: check the moved blocks and that you
kept the same `lab/` state. A module source edit alone does not tell Terraform these are the same objects.

## 3. Apply and verify

```text
terraform apply build/modules.tfplan
terraform state list
terraform state show module.storage.aws_s3_bucket.assets
python ../scripts/aws_local.py s3api list-buckets
python ../scripts/lab.py smoke-api
terraform plan
```

Expect the same bucket names, successful order processing, and a clean plan.
Keep `moved` blocks in the shared course so learners upgrading from the earlier layout retain the migration.

**Checkpoint:** Both buckets have module addresses without replacement, the order flow passes, and the final plan is clean.

**Exercise:** draw how the child input and output connect to the root locals. Propose a messaging module
interface on paper; do not refactor everything at once.
**Troubleshooting:** `Module not installed` means rerun `init`; unexpected destroys mean inspect state
addresses and moves before applying.

Source: [HashiCorp module refactoring](https://developer.hashicorp.com/terraform/language/modules/develop/refactoring).
