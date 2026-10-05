# 13 — Remote state in Floci S3 (optional)

[Previous](12-modules.md) · [Index](../README.md) · [Next: cleanup](14-cleanup.md)

**Goal:** migrate application state to a local S3 backend, try locking, then migrate it back.
**Start:** Chapter 12 passed; Terraform 1.10+ (the pinned 1.16.5 qualifies); Floci running.
This backend is remote relative to the Terraform process, but still on your machine. It is not an
off-machine backup or a multi-user cloud service.

## 1. Understand the bootstrap problem

Terraform must initialize its backend before it can manage application resources. Therefore the
backend bucket must already exist. Use a **separate root module and state** for that bucket.
The provider configuration in `lab/providers.tf` does not configure the S3 backend: it has its own
endpoints and fake credentials. Backend blocks cannot use ordinary input-variable/resource references.

From repository root, create `state-bootstrap/` and copy [the bootstrap file](../examples/13-bootstrap/main.tf)
and its [provider lock file](../examples/13-bootstrap/.terraform.lock.hcl). This separate root module
needs its own lock file to select the same tested AWS provider as the main lab. Terraform otherwise
selects the newest provider allowed by the constraint on its first initialization.
PowerShell and Bash both support these Python commands:

```text
python -c "from pathlib import Path; import shutil; Path('state-bootstrap').mkdir(exist_ok=True); shutil.copyfile('examples/13-bootstrap/main.tf','state-bootstrap/main.tf')"
python -c "import shutil; shutil.copyfile('examples/13-bootstrap/.terraform.lock.hcl','state-bootstrap/.terraform.lock.hcl')"
cd state-bootstrap
terraform init
terraform fmt
terraform validate
terraform plan "-out=bootstrap.tfplan"
terraform show bootstrap.tfplan
```

Expect **2 additions**: a bucket and its versioning configuration. Review, then:

```text
terraform apply bootstrap.tfplan
python ../scripts/aws_local.py s3api get-bucket-versioning --bucket terraform-workshop-state
cd ../lab
```

## 2. Migrate local application state

Back up the existing local state without changing its contents, then copy the backend configuration:

```text
python -c "import shutil; shutil.copyfile('terraform.tfstate','generated/pre-remote.tfstate')"
python -c "import shutil; shutil.copyfile('../examples/13-backend/backend.tf','backend.tf')"
terraform init -migrate-state
```

Read the migration prompt and answer `yes` to copy the existing state to this local bucket.
Do not use `-reconfigure` as a substitute: it does not perform this state migration.

```text
terraform state list
terraform plan
python ../scripts/aws_local.py s3api list-objects-v2 --bucket terraform-workshop-state --prefix orders/
```

Expect the same addresses, no resource changes, and `orders/terraform.tfstate` in S3.
Do not commit the backup, state objects, or plan files. Sensitive values remain present in state.

## 3. Observe locking

The backend has `use_lockfile = true`, enabling S3 lock objects. Historical examples used a DynamoDB
table with a `LockID` key; that locking mechanism is deprecated in current Terraform. This chapter uses S3 locking.

In terminal A, in `lab/`, run:

```text
terraform apply "-var=demo_secret_note=lock-demo"
```

Leave it waiting at the approval prompt; **do not approve** the change. In terminal B, in the same `lab/`:

```text
terraform plan "-lock-timeout=5s"
```

Expect a lock-acquisition error while A holds the lock. Answer `no` in A, then rerun the plan in B;
it should succeed. Never force-unlock an operation that is still running. The `.tflock` object is
transient and is distinct from `.terraform.lock.hcl`, which locks provider dependency selections.

## 4. Migrate back before cleanup

This chapter deliberately ends with local application state again:

```text
python -c "from pathlib import Path; Path('backend.tf').rename('backend.tf.disabled')"
terraform init -migrate-state
terraform state list
terraform plan
```

Answer `yes` when asked to migrate back. Confirm the same resources and a clean plan before destroying
the bootstrap bucket. Renaming backend configuration is allowed; manually editing state is not.

**Checkpoint:** round-trip migration preserved addresses; locking was observed; local backend restored.
**Exercise:** explain why deleting the backend bucket first could leave Terraform unable to find its state.
**Troubleshooting:** if the pinned emulator rejects backend or lock operations, preserve the existing state
and stop this optional exercise. Follow the error's migration instructions; do not force-copy, force-unlock,
or delete state to bypass it. Return to a verified backend before continuing cleanup.

Sources: [HashiCorp S3 backend and locking](https://developer.hashicorp.com/terraform/language/backend/s3)
and [provider lock files](https://developer.hashicorp.com/terraform/language/files/dependency-lock).
