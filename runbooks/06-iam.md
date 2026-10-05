# 06 — IAM roles and policies

[Previous](05-configuration-secrets.md) · [Index](../README.md) · [Next](07-lambda.md)

**Goal:** describe what the Lambda service may assume and what function code may access.
**Prerequisite:** Chapter 05 passed.

## 1. Prepare this chapter

Start at the repository root. If still inside `lab/`, first run `cd ..`.

```text
python scripts/chapter.py 6
cd lab
```

Inspect the [new/replaced reference files](../examples/06/). The copier preserves state and
personal tfvars, and backs up overwritten source under `.workshop/backups/`.

`aws_iam_role.lambda.assume_role_policy` trusts the Lambda service to assume the role.
`aws_iam_policy.lambda` grants actions on the lab tables, orders queue, topics, archive objects,
and Lambda log streams. `aws_iam_role_policy_attachment.lambda` connects the policy to the role.
A trust policy answers **who can assume**; a permissions policy answers **what the assumed role can do**.

Inspect each ARN reference. The logs pattern limits names to this lab prefix; the archive `/*`
matches objects, not the bucket resource. Both functions share a role to keep this lesson small;
production designs normally separate their permissions. Emulator policy acceptance is not a security audit.
The Python teaching workload uses explicit fake SDK credentials; local execution does not prove IAM enforcement.

## 2. Review the plan and apply

```text
terraform init
terraform fmt -recursive
terraform validate
terraform plan "-out=build/chapter06.tfplan"
terraform show build/chapter06.tfplan
```

Expect **3 additions**: role, policy, attachment. No function runs in this chapter.
If you deliberately changed the prefix, use `terraform output -raw lambda_role_name` in the CLI command.

Only after those changes match your expectations:

```text
terraform apply build/chapter06.tfplan
terraform state list
terraform output
```

## 3. Verify and finish

```text
python ../scripts/aws_local.py iam list-roles
python ../scripts/aws_local.py iam list-policies --scope Local
python ../scripts/aws_local.py iam list-attached-role-policies --role-name terraform-lab-dev-lambda
terraform state show aws_iam_role_policy_attachment.lambda
terraform plan
```

The final plan should report no changes. A saved plan is a snapshot: after editing configuration,
discard the old plan and generate a new one before applying.

**Checkpoint:** The Lambda role has its managed policy attached, and the final plan is clean.

**Exercise:** Locate the statement granting `s3:PutObject` and explain why its Resource ends with `/*`.
Which statements would the create-order and process-order functions need if roles were separated?

**Troubleshooting:** A role ARN is different from its name. `list-attached-role-policies` needs the role name;
the Lambda Terraform resource in the next chapter needs its ARN.
