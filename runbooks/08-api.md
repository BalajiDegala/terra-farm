# 08 — API Gateway and deployment lifecycle

[Previous](07-lambda.md) · [Index](../README.md) · [Next](09-events.md)

**Goal:** expose `POST /orders` locally. **Prerequisite:** Chapter 07's smoke test passed.

## 1. Prepare this chapter

Start at the repository root. If still inside `lab/`, first run `cd ..`.

```text
python scripts/chapter.py 8
cd lab
```

Inspect the [new/replaced reference files](../examples/08/). The copier preserves state and
personal tfvars, and backs up overwritten source under `.workshop/backups/`.

`api.tf` defines a REST API using an OpenAPI document. Its extension connects POST /orders to
the create-order Lambda using an AWS proxy integration. This keeps route/method/integration configuration
in one inspectable document rather than several separate Terraform resources.

Lambda permission allows API Gateway to invoke this function for the matching route. A deployment
captures API configuration, and a stage points at that deployment. The body hash in `triggers` schedules
a new deployment when the API changes. `create_before_destroy` creates the replacement before removing
the old deployment, allowing the stage to change references first.

The pinned Floci/provider combination also has a tag read-back mismatch for API stages. This chapter
adds the API Gateway endpoint to `aws.untagged` and selects that alias for the stage. The REST API
keeps its normal tags; infrastructure drift remains visible without an `ignore_changes` rule.

Use the `api_endpoint` Terraform output: Floci's local REST invocation path differs from real AWS.
The route is intentionally unauthenticated for a localhost lesson; it is not an internet deployment.

## 2. Review the plan and apply

```text
terraform init
terraform fmt -recursive
terraform validate
terraform plan "-out=build/chapter08.tfplan"
terraform show build/chapter08.tfplan
```

Expect **4 additions**: REST API, Lambda permission, deployment, stage.
The smoke helper sends HTTP JSON to the output URL. Expect HTTP 202 followed by the same
PROCESSED/archive/notification checks as Chapter 07.

Only after those changes match your expectations:

```text
terraform apply build/chapter08.tfplan
terraform state list
terraform output
```

## 3. Verify and finish

```text
python ../scripts/aws_local.py apigateway get-rest-apis
terraform output -raw api_endpoint
python ../scripts/lab.py smoke-api
terraform plan
```

The final plan should report no changes. A saved plan is a snapshot: after editing configuration,
discard the old plan and generate a new one before applying.

**Checkpoint:** POST /orders returns HTTP 202 and completes the order flow; the final plan is clean.

**Exercise:** Change the OpenAPI `info.version`, plan, and find the deployment replacement. Explain the
`+/-` create-before-destroy marker. Restore it before applying if you only want to inspect the plan.

**Troubleshooting:** A 404 often means the wrong invocation path or stage. Read the output, not an AWS URL template.
A 502 means inspect the Lambda response/logs. Do not count a successful API creation as an invocation test.
