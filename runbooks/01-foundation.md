# 01 — Terraform foundation

[Previous](00-setup.md) · [Index](../README.md) · [Next](02-storage-database.md)

**Goal:** configure Terraform and prove its AWS provider reads from Floci.
**Start:** Chapter 00 passed; terminal at repository root; `lab/` does not yet exist.

## 1. Prepare and inspect

```text
python scripts/chapter.py 1
cd lab
```

Inspect the [reference files](../examples/01/). They are now your editable files in `lab/`.

| File/block | What it means |
| --- | --- |
| `versions.tf`: `terraform` | CLI constraints and provider requirements; no remote backend yet |
| `required_providers.aws` | Local provider name `aws`, registry source `hashicorp/aws`, allowed version range |
| `providers.tf`: `provider "aws"` | Fake credentials, local endpoints, path-style S3, common tags |
| `variables.tf`: `variable` | Inputs with types, descriptions, defaults, and validation |
| `locals.tf`: `locals` | Computed names/tags used throughout the project |
| `outputs.tf`: `output` | Values Terraform exposes to the learner and later tooling |
| `terraform.tfvars.example` | Optional input example; this filename is not automatically loaded |

`~> 6.0` permits provider 6.x, not 7.x. `.terraform.lock.hcl` fixes the selected version and hashes;
commit it. Do not use `init -upgrade` during this course unless deliberately reviewing an upgrade.
All `.tf` files in a directory form one root module; filenames do not set execution order.

Five inputs control the lab: `project_name`, `environment`, `aws_region`, `floci_endpoint`, `common_tags`.
The endpoint accepts only localhost or 127.0.0.1 on port 4566. Keep `us-east-1` for the supplied exercises.
`lower(replace(...))` normalizes names; `format()` joins project and environment; `merge()` lets the lab's
reserved Project/Environment/ManagedBy tags win over extra tags. `nullable = false` rejects explicit nulls.

The provider skips ordinary AWS credential validation, metadata discovery, and automatic account discovery.
An explicit `data "aws_caller_identity" "local"` still calls Floci STS. Its postcondition requires the
emulator account. A **data source reads**; a **resource manages** an object. No resource is created here.
The local credentials files keep your personal AWS configuration out of this provider.
Every service introduced later must also get an explicit local endpoint.

## 2. Initialize, format, validate, plan

```text
terraform init
terraform fmt -recursive
terraform validate
terraform plan "-out=build/chapter01.tfplan"
terraform show build/chapter01.tfplan
```

`init` downloads the provider; `fmt` formats HCL; `validate` checks structure; `plan` reads current
data and proposes changes. Registry downloads use the internet; AWS API requests use Floci.
Keep the quotes around arguments such as `"-out=build/chapter01.tfplan"`. They ensure Windows
PowerShell passes each option as one argument and work unchanged in macOS/Linux shells.
Expect `data.aws_caller_identity.local: Read complete` and `Changes to Outputs` including
`local_account_id = "000000000000"` and `name_prefix = "terraform-lab-dev"`.
There should be no managed-resource creations, updates, or deletions.

## 3. Save outputs and inspect state

After reviewing that plan:

```text
terraform apply build/chapter01.tfplan
terraform output
terraform state list
terraform state show data.aws_caller_identity.local
python ../scripts/aws_local.py sts get-caller-identity
terraform plan
```

Apply saves the data-source result and outputs into local `terraform.tfstate`. The final plan should
report no changes. State binds configuration addresses to observed objects; never edit it by hand.

**Checkpoint:** Terraform and AWS CLI report the same local identity; the plan converges.
**Exercise:** copy `terraform.tfvars.example` to `terraform.tfvars` in your editor, change
`project_name` to `My_Shop`, and predict `name_prefix`. Run `terraform plan` to check.
Restore/delete that personal tfvars file before proceeding so the published names match later commands.
Do not apply the exercise's naming change. `terraform.tfvars` overrides variable defaults automatically.
**If blocked:** install/provider errors belong to initialization; a refused STS connection means check Floci.

Sources: [provider configuration](https://floci.io/floci/getting-started/terraform/),
[variables](https://developer.hashicorp.com/terraform/language/values/variables),
[version constraints](https://developer.hashicorp.com/terraform/language/expressions/version-constraints).
