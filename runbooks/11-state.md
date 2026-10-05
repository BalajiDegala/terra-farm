# 11 — Drift, import, and replacement

[Previous](10-expressions.md) · [Index](../README.md) · [Next](12-modules.md)

**Goal:** distinguish configuration, recorded state, and actual infrastructure.
**Start:** Chapter 10 complete, healthy Floci, no running order tests. Repository root:

```text
python scripts/chapter.py 11
cd lab
terraform state list
terraform state show aws_sqs_queue.orders
terraform plan
```

A clean plan is the starting checkpoint. Back up `terraform.tfstate` using your file manager;
keep the copy private/ignored. Do not edit state, delete it, or use `state rm` to work around this lesson.
`terraform show` displays a human-readable state snapshot; secret values may be present in stored state.

## 1. Introduce and repair drift

```text
python ../scripts/lab.py drift
terraform plan "-out=build/drift.tfplan"
terraform show build/drift.tfplan
```

The helper runs `aws --endpoint-url http://localhost:4566 sqs set-queue-attributes` and changes
the orders queue's VisibilityTimeout to 60. Configuration still says 180. Expect an in-place `~`
change from 60 back to 180, without queue replacement.

```text
terraform apply build/drift.tfplan
terraform state show aws_sqs_queue.orders
terraform plan
```

The final plan should be clean. A normal plan refreshes observations before comparing with desired
configuration; the state file is a record, not the desired-state source.

## 2. Adopt an object with import

```text
python ../scripts/lab.py import-create
```

This creates a local SSM parameter outside Terraform and prints its import ID.
Create `lab/imported.tf` in your editor:

```hcl
resource "aws_ssm_parameter" "imported_note" {
  name  = "/${local.name_prefix}/imported-note"
  type  = "String"
  value = "created-outside-terraform"
}
```

For the default project prefix, run:

```text
terraform fmt
terraform validate
terraform import aws_ssm_parameter.imported_note /terraform-lab-dev/imported-note
terraform state show aws_ssm_parameter.imported_note
terraform plan "-out=build/import.tfplan"
terraform show build/import.tfplan
```

If you changed the prefix, use the **exact ID printed by the helper**. Do not apply a creation plan
for this parameter before importing it. Import associates the existing object with an address;
it does not create the HCL or automatically make it match. The plan may add the provider's default
tags in place. Review and apply `build/import.tfplan`, then confirm a clean plan.
Keep `imported.tf` for later cleanup: Terraform now manages this parameter too.

## 3. Request a deliberate replacement

```text
terraform plan "-replace=local_file.app_config" "-out=build/replace.tfplan"
terraform show build/replace.tfplan
```

Expect `-/+` on the local generated file: remove/recreate even though its content need not change.
Existing cloud resources should remain intact. After reviewing:

```text
terraform apply build/replace.tfplan
python -m json.tool generated/app-config.json
terraform plan
```

`terraform apply "-replace=local_file.app_config"` is the interactive equivalent. The saved-plan flow
separates review from execution. `terraform taint` is an older workflow; prefer `-replace`.

**Checkpoint:** drift repaired; imported parameter managed; file replacement completed; final plan clean.
**Exercise:** explain why import changed Terraform's ownership record while drift repair changed the queue.
**Troubleshooting:** if import says already managed, inspect state instead of importing twice. If the helper
says parameter exists, inspect it and continue with the import; do not overwrite unknown data.
