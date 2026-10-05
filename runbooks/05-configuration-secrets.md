# 05 — Parameters, secrets, and encryption

[Previous](04-messaging.md) · [Index](../README.md) · [Next](06-iam.md)

**Goal:** centralize application settings and understand sensitive state. **Prerequisite:** Chapter 04 passed.

## 1. Prepare this chapter

Start at the repository root. If still inside `lab/`, first run `cd ..`.

```text
python scripts/chapter.py 5
cd lab
```

Inspect the [new/replaced reference files](../examples/05/). The copier preserves state and
personal tfvars, and backs up overwritten source under `.workshop/backups/`.

`parameters.tf` uses `for_each` over a map of three settings. `each.key` determines the parameter
path and `each.value` comes from variables or resource references. A sample address is
`aws_ssm_parameter.app["environment"]`.

`secrets.tf` adds a fake generated password, KMS key/alias, and secret metadata/version.
The key ARN connects the secret to its encryption key; the alias is a readable name for the key.
The secret resource describes the container; its version holds the JSON value.
`sensitive = true` suppresses routine display of `demo_secret_note`; it does **not** encrypt Terraform
state. Keep state/plans/backups out of Git. Use fake values only; do not print the secret version in a
screen share. The secret is a configuration lesson, not a real payment-provider credential.

## 2. Review the plan and apply

```text
terraform init
terraform fmt -recursive
terraform validate
terraform plan "-out=build/chapter05.tfplan"
terraform show build/chapter05.tfplan
```

Expect **8 additions**: three parameters, a password, key, alias, secret, and version.
The secret value should be shown as sensitive. Verify the parameter paths and key alias match the prefix.

Only after those changes match your expectations:

```text
terraform apply build/chapter05.tfplan
terraform state list
terraform output
```

## 3. Verify and finish

```text
python ../scripts/aws_local.py ssm describe-parameters
python ../scripts/aws_local.py secretsmanager list-secrets
python ../scripts/aws_local.py kms list-aliases
terraform state list
terraform plan
```

The final plan should report no changes. A saved plan is a snapshot: after editing configuration,
discard the old plan and generate a new one before applying.

**Checkpoint:** All three parameters, the fake secret, and the KMS alias exist; the final plan is clean.

**Exercise:** Add a nonsecret `app/team` entry to `local.parameters`, plan, and identify its stable string-key
address. Restore the file before continuing, or apply and record the intentional extra resource.

**Troubleshooting:** A missing KMS/Secrets/SSM operation is a compatibility issue, not a reason to point at AWS.
Check the pinned image and record the failing API name; remain on the previous working checkpoint.
