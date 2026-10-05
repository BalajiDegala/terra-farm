# 14 — Destroy, verify, and repeat

[Previous](13-remote-state.md) · [Course index](../README.md)

**Goal:** remove the resources managed by your lab using Terraform's dependency graph.
**Start:** Floci still running. Use this chapter from any earlier completed chapter if stopping early.
If you completed remote state, first finish its migration back to local. Keep all state/configuration files.

## 1. Review destruction

From `lab/`:

```text
terraform plan -destroy "-out=build/destroy.tfplan"
terraform show build/destroy.tfplan
```

Read every deletion. Terraform generally removes dependents before their dependencies: event-source
mappings before queues/functions, API stages before deployments, subscriptions before topics/queues,
and policy attachments before roles. Independent branches may run in parallel.

With the default full course plus import, expect **37 managed resources** to be destroyed. Counts differ
if you stopped early or kept extra exercises. Archive data and test objects will be removed because
these lab buckets use `force_destroy`; the fake secret has immediate deletion configured. A KMS key
may remain in PendingDeletion during its configured deletion window, even after Terraform removes it from state.

After confirming that only your lab resources are in the plan:

```text
terraform apply build/destroy.tfplan
terraform state list
```

`terraform destroy` is the interactive equivalent, showing a destroy plan and asking for confirmation.
The saved-plan form applies exactly the reviewed destruction plan. A follow-up ordinary `terraform plan`
would propose rebuilding the project; that is expected after destroy, not proof of failed cleanup.

### If archive bucket deletion keeps retrying

During validation with Floci 2.1.0 and AWS provider 6.67.0, the archive bucket sometimes retained
test-order objects despite `force_destroy`. The other resources were removed, but Terraform kept
retrying that bucket. If this happens, cancel the running apply once with Ctrl+C and **wait for it to
exit** before running another Terraform command. Keep its state.

Run `terraform state list`, then inspect the remaining bucket with
`terraform state show module.storage.aws_s3_bucket.order_archive` (before Chapter 12, use
`aws_s3_bucket.order_archive`). Use the exact bucket name shown in that state. For the default names:

```text
python ../scripts/aws_local.py s3api get-bucket-versioning --bucket terraform-lab-dev-archive
python ../scripts/aws_local.py s3api list-objects-v2 --bucket terraform-lab-dev-archive
```

The course archive bucket is unversioned: versioning should have no `Status`, and the objects should
be your disposable test orders. After checking those results, remove the test objects and review a
fresh destroy plan:

```text
python ../scripts/aws_local.py s3 rm s3://terraform-lab-dev-archive --recursive
terraform plan -destroy "-out=build/destroy.tfplan"
terraform show build/destroy.tfplan
terraform apply build/destroy.tfplan
terraform state list
```

If you customized the project name, substitute the bucket from state in all three AWS commands.
This recovery applies to the unversioned application archive; a bucket with versioning enabled or
suspended needs a different recovery because `s3 rm` does not remove all stored versions. Keep the
separate backend bucket until application state is local and follow section 3 for its cleanup.

## 2. Verify the emulator

```text
python ../scripts/aws_local.py s3api list-buckets
python ../scripts/aws_local.py dynamodb list-tables
python ../scripts/aws_local.py sqs list-queues
python ../scripts/aws_local.py sns list-topics
python ../scripts/aws_local.py lambda list-functions
python ../scripts/aws_local.py iam list-roles
python ../scripts/aws_local.py ssm describe-parameters
python ../scripts/aws_local.py secretsmanager list-secrets
python ../scripts/aws_local.py logs describe-log-groups
python ../scripts/aws_local.py apigateway get-rest-apis
python ../scripts/aws_local.py events list-event-buses
python ../scripts/aws_local.py kms list-aliases
```

Expect your lab-prefixed entries to be absent and no managed resources in state. Floci may retain
built-in entries such as the default event bus. The optional state bucket remains until the next step.
Use `kms describe-key --key-id <previous-key-id>` if auditing its scheduled deletion; loss of Terraform
ownership is not the same as immediate physical KMS deletion.

## 3. Remove the optional bootstrap project

Skip this section if you did not do Chapter 13. Confirm application state is local first, then:

```text
cd ../state-bootstrap
terraform plan -destroy "-out=bootstrap-destroy.tfplan"
terraform show bootstrap-destroy.tfplan
```

This removes the two bootstrap resources, **including stored state-object versions** through the
bucket's `force_destroy` setting. Preserve any backup you need before proceeding.

```text
terraform apply bootstrap-destroy.tfplan
terraform state list
python ../scripts/aws_local.py s3api list-buckets
cd ..
```

## 4. Stop Floci last

From repository root:

```text
docker compose -f compose.yaml -f compose.lambda.yaml stop floci
```

This preserves the emulator volume. Do not use Docker volume deletion as a substitute for Terraform
cleanup, and do not remove Terraform state before removing its resources.

To rebuild the final architecture, start Floci with the same two Compose files, go to `lab/`, then run
`terraform init`, `terraform plan "-out=build/rebuild.tfplan"`, review, and apply that plan. Run `smoke-api` again.
To repeat the curriculum from Chapter 01 instead, after confirmed destruction archive your `lab/` directory
outside the working location using your file manager, then run `python scripts/chapter.py 1` from repository root.
The copier refuses to reset a nonempty lab so it cannot silently overwrite your state.

**Checkpoint:** application resources removed; optional backend removed; Floci stopped last.
**Exercise:** explain which files you need to retain to resume an unfinished lab and why a Git checkout alone
does not restore the infrastructure-to-state mapping.
**Troubleshooting:** if destroy fails, keep state and Floci running. Fix the reported dependency or operation,
make a new destroy plan, and retry. Do not fall back to deleting the entire emulator volume.
