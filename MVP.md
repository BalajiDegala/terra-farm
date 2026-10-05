# Terraform + Floci Learning Project — MVP

> Delivery clarification (2026-10-03): this repository is a portable, chapter-based
> workshop for learners on their own machines. The README and runbooks are the
> current entry point. The phase-by-phase agent instructions below are the original
> design brief, not a requirement to run the course on the author's machine.

Delivery: [MVP 0.1.0 acceptance mapping](runbooks/acceptance.md),
[reproducible maintainer checks](runbooks/maintaining.md), and
[validation evidence](runbooks/validation.md).

## 1. Project Name

**terraform-floci-lab**

## 2. Goal

Build a practical Terraform learning project that provisions a realistic local AWS-style application infrastructure using **Floci**.

The project must:

- Use Terraform as the Infrastructure as Code tool.
- Use Floci instead of a real AWS account.
- Create approximately **20–30 meaningful Terraform resources**.
- Use multiple Terraform providers.
- Teach Terraform incrementally while building the project.
- Avoid creating billable resources in real AWS.
- Produce a working local infrastructure lab that can be destroyed and recreated using Terraform.

The sample workload will represent a small **e-commerce / order-processing application**.

---

## 3. Local Cloud

Floci endpoint:

```text
http://localhost:4566
```

Use fake local AWS credentials:

```bash
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
export AWS_DEFAULT_REGION=us-east-1
```

Never require real AWS credentials.

---

## 4. MVP Architecture

```text
                   +------------------+
                   |      Client      |
                   +--------+---------+
                            |
                            v
                   +------------------+
                   |   API Gateway    |
                   +--------+---------+
                            |
                            v
                   +------------------+
                   | Create Order     |
                   | Lambda           |
                   +---+----------+---+
                       |          |
                       |          |
                       v          v
                +----------+   +-----------+
                | DynamoDB |   |    SQS    |
                | Orders   |   | Orders Q  |
                +----------+   +-----+-----+
                                   |
                                   v
                            +--------------+
                            | Process Order|
                            | Lambda       |
                            +------+-------+
                                   |
                                   v
                            +--------------+
                            |     SNS      |
                            | Order Events |
                            +------+-------+
                                   |
                                   v
                            +--------------+
                            | Notification |
                            | SQS Queue    |
                            +--------------+
```

Supporting infrastructure:

```text
S3
IAM
SSM Parameter Store
Secrets Manager
KMS
CloudWatch Logs
EventBridge
Local generated configuration
Random resource naming
```

---

# 5. Required Terraform Providers

The project should use these providers where appropriate.

## AWS

```hcl
hashicorp/aws
```

Purpose:

- S3
- DynamoDB
- SQS
- SNS
- IAM
- Lambda
- SSM
- Secrets Manager
- KMS
- CloudWatch
- EventBridge
- API Gateway

Configure AWS service endpoints to use Floci.

Example provider configuration:

```hcl
provider "aws" {
  region     = var.aws_region
  access_key = "test"
  secret_key = "test"

  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true

  s3_use_path_style = true

  endpoints {
    s3       = var.floci_endpoint
    dynamodb = var.floci_endpoint
    sqs      = var.floci_endpoint
    sns      = var.floci_endpoint
  }
}
```

Add service endpoints as services are introduced.

Do not configure unsupported Floci services without first checking compatibility.

---

## Random

```hcl
hashicorp/random
```

Use for meaningful generated values such as:

```text
bucket suffix
application identifier
development-only generated password
```

Possible resources:

```hcl
random_id
random_string
random_password
random_pet
```

Do not add random resources purely to increase the resource count.

---

## Local

```hcl
hashicorp/local
```

Use:

```hcl
local_file
```

Generate:

```text
generated/app-config.json
```

The generated configuration must obtain values from Terraform resources.

Example output:

```json
{
  "environment": "dev",
  "orders_table": "terraform-lab-dev-orders",
  "orders_queue": "...",
  "assets_bucket": "..."
}
```

---

## Archive

```hcl
hashicorp/archive
```

Use to package Lambda source code.

Example:

```hcl
data "archive_file" "create_order" {
  type        = "zip"
  source_dir  = "${path.module}/lambda/create_order"
  output_path = "${path.module}/build/create_order.zip"
}
```

This provider should also be used to teach the difference between a Terraform **resource** and a **data source**.

---

# 6. MVP Resource Target

Create approximately **20–30 meaningful resources**.

The exact total may change depending on Floci support.

## Storage

### S3

1. Application assets bucket
2. Order archive bucket

Possible Terraform resources:

```text
aws_s3_bucket.assets
aws_s3_bucket.order_archive
```

---

## Database

### DynamoDB

3. Orders table
4. Products table

Keys:

```text
Orders
  order_id

Products
  product_id
```

Terraform concepts:

```text
hash_key
attributes
billing_mode
references
```

---

## Messaging

### SQS

5. Order processing queue
6. Order dead-letter queue
7. Notification queue

Teach:

```text
queue URL
queue ARN
redrive_policy
jsonencode()
resource references
```

### SNS

8. Order events topic
9. Order failures topic
10. SNS -> SQS subscription, if supported

Teach:

```text
topic ARN
subscriptions
event-driven architecture
```

---

## IAM

11. Lambda execution role
12. Lambda permissions policy
13. Role-policy attachment

Teach:

```text
IAM role
assume role policy
IAM policy
ARN
jsonencode()
```

---

## Lambda

14. Create-order Lambda
15. Process-order Lambda

Use simple Python handlers.

Teach:

```text
archive_file
source_code_hash
environment variables
resource dependencies
IAM role references
```

---

## SSM Parameter Store

16. `/shop/environment`
17. `/shop/orders/table-name`
18. `/shop/orders/queue-name`

Values should reference Terraform-created infrastructure instead of duplicating names.

---

## Secrets Manager

19. Application secret
20. Secret version

Use fake local development data only.

Never store real credentials in the repository.

Explain that sensitive values can still exist inside Terraform state.

---

## KMS

21. Application KMS key
22. KMS alias

Teach:

```text
key ID
ARN
aliases
cross-resource references
```

---

## CloudWatch

23. Create-order Lambda log group
24. Process-order Lambda log group

Teach:

```text
log groups
retention
conditional expressions
```

---

## EventBridge

25. Custom event bus
26. Order event rule
27. Event target

Create only if the corresponding Floci operations are supported.

---

## API Gateway

Possible additional resources:

28. REST/HTTP API
29. API route/resource
30. Lambda integration / permission

API Gateway may require several Terraform resources.

The project does **not** need exactly 30 resources.

The priority is useful infrastructure, not resource count.

---

# 7. Required Terraform Concepts

The MVP must demonstrate the following concepts.

## Initialization

```bash
terraform init
terraform fmt
terraform validate
terraform plan
terraform apply
terraform destroy
```

---

## Providers

Teach:

```text
terraform block
required_providers
provider configuration
provider version constraints
```

---

## Resources

Teach syntax:

```hcl
resource "aws_s3_bucket" "assets" {
  bucket = "..."
}
```

Explain resource addresses:

```text
aws_s3_bucket.assets
```

---

## Variables

Create:

```text
variables.tf
```

Required variables:

```hcl
project_name
environment
aws_region
floci_endpoint
common_tags
```

Teach:

```text
type
description
default
validation
sensitive
```

---

## tfvars

Create:

```text
terraform.tfvars.example
```

Never include real secrets.

---

## Locals

Create:

```text
locals.tf
```

Example:

```hcl
locals {
  name_prefix = "${var.project_name}-${var.environment}"

  common_tags = merge(
    var.common_tags,
    {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  )
}
```

Teach the difference between:

```text
variables
locals
outputs
```

---

## Outputs

Create:

```text
outputs.tf
```

Useful outputs:

```text
assets bucket name
archive bucket name
orders table name
products table name
orders queue URL
notification queue URL
SNS topic ARN
Lambda function names
API endpoint
```

---

## Resource References

Use expressions such as:

```hcl
aws_dynamodb_table.orders.name

aws_sqs_queue.orders.url

aws_sns_topic.order_events.arn
```

Explain how references automatically create Terraform dependencies.

---

## Dependency Graph

Teach:

```text
implicit dependencies
explicit depends_on
```

Prefer implicit dependencies.

Use `depends_on` only when Terraform cannot infer the relationship.

---

## for_each

Use at least one meaningful example.

Example:

```hcl
locals {
  parameters = {
    environment = var.environment
    table       = aws_dynamodb_table.orders.name
    queue       = aws_sqs_queue.orders.url
  }
}

resource "aws_ssm_parameter" "app" {
  for_each = local.parameters

  name  = "/shop/${each.key}"
  type  = "String"
  value = each.value
}
```

Explain addresses such as:

```text
aws_ssm_parameter.app["environment"]
```

---

## count

Use one simple example for learning purposes.

Then explain why `for_each` is usually easier to maintain for individually named resources.

---

## Conditionals

Use:

```hcl
condition ? true_value : false_value
```

Example:

```hcl
retention_in_days = var.environment == "prod" ? 30 : 7
```

---

## Terraform Functions

Use practical examples of:

```text
jsonencode()
merge()
format()
lower()
replace()
toset()
lookup()
try()
templatefile()
```

Do not add unnecessary complexity just to demonstrate a function.

---

## Data Sources

Use at least:

```hcl
data "archive_file"
```

Teach:

```text
resource = Terraform manages something

data = Terraform reads/calculates something
```

---

## Templates

Create:

```text
templates/app-config.json.tftpl
```

Use:

```hcl
templatefile()
```

---

## Lifecycle

Teach:

```hcl
lifecycle {
}
```

Explain:

```text
create_before_destroy
prevent_destroy
ignore_changes
```

Use a lifecycle rule only where it makes sense.

---

# 8. State Learning Requirements

State is an important part of this project.

Teach:

```bash
terraform state list

terraform state show aws_s3_bucket.assets

terraform show
```

Explain:

```text
terraform.tfstate
configuration
state
actual infrastructure
resource address
drift
```

Never manually edit the `.tfstate` file.

---

# 9. Drift Exercise

After Terraform creates a resource:

1. Modify a supported resource outside Terraform using AWS CLI.
2. Run:

```bash
terraform plan
```

3. Observe the difference.
4. Explain infrastructure drift.
5. Restore the desired state using Terraform.

---

# 10. Import Exercise

Perform at least one import exercise.

Workflow:

1. Create a supported Floci resource manually.
2. Add matching Terraform configuration.
3. Import it.

Example:

```bash
terraform import RESOURCE_ADDRESS RESOURCE_ID
```

4. Run:

```bash
terraform plan
```

5. Make configuration match the imported resource.

---

# 11. Replace Exercise

Teach:

```bash
terraform apply -replace="RESOURCE_ADDRESS"
```

Explain how this differs from a normal update.

Mention `terraform taint` as an older workflow rather than the preferred approach.

---

# 12. Terraform Console

Practice:

```bash
terraform console
```

Example expressions:

```hcl
upper("dev")

lower("MY-APP")

toset(["one", "two", "two"])

merge(
  { Environment = "dev" },
  { ManagedBy = "Terraform" }
)

jsonencode({
  app = "shop"
})
```

---

# 13. Terraform Graph

Teach:

```bash
terraform graph
```

If Graphviz is available:

```bash
terraform graph | dot -Tpng > terraform-graph.png
```

Explain Terraform's dependency DAG.

---

# 14. Modules

Do not begin the project with modules.

First build the infrastructure using normal Terraform resources.

After the user understands the resources, refactor suitable sections into:

```text
modules/
├── storage/
├── database/
└── messaging/
```

Teach:

```text
root module
child module
input variable
module output
module reference
```

Example:

```hcl
module "storage" {
  source = "./modules/storage"

  project_name = var.project_name
  environment  = var.environment
}
```

---

# 15. Remote State Exercise

After the normal project works, create a separate learning exercise covering remote state.

Where Floci supports the required operations, demonstrate an S3 backend.

Also explain the historical use of DynamoDB for state locking and current Terraform backend locking behavior.

This must be a later exercise because backend infrastructure needs to exist before Terraform can use it.

Explain the bootstrap problem.

---

# 16. Folder Structure

Target structure:

```text
terraform-floci-lab/
│
├── README.md
├── MVP.md
├── .gitignore
│
├── versions.tf
├── providers.tf
├── variables.tf
├── terraform.tfvars.example
├── locals.tf
├── outputs.tf
│
├── storage.tf
├── database.tf
├── messaging.tf
├── iam.tf
├── lambda.tf
├── parameters.tf
├── secrets.tf
├── events.tf
├── api.tf
│
├── lambda/
│   ├── create_order/
│   │   └── handler.py
│   └── process_order/
│       └── handler.py
│
├── templates/
│   └── app-config.json.tftpl
│
├── generated/
│
├── build/
│
└── modules/
    ├── storage/
    │   ├── main.tf
    │   ├── variables.tf
    │   └── outputs.tf
    │
    ├── database/
    │   ├── main.tf
    │   ├── variables.tf
    │   └── outputs.tf
    │
    └── messaging/
        ├── main.tf
        ├── variables.tf
        └── outputs.tf
```

Only create files as they become necessary.

---

# 17. Git Requirements

Initialize a Git repository.

Create `.gitignore`.

Ignore:

```gitignore
.terraform/
*.tfstate
*.tfstate.*
crash.log
crash.*.log
*.tfplan
build/
generated/
```

Do **not** ignore:

```text
.terraform.lock.hcl
```

Explain why provider dependency locks should normally be committed.

---

# 18. Learning Phases

Codex must develop the project incrementally.

## Phase 0 — Environment

Verify:

```bash
terraform version
docker --version
docker compose version
aws --version
```

Start Floci.

Verify:

```bash
curl http://localhost:4566
```

Verify AWS CLI can communicate with Floci.

Do not create application resources yet.

---

## Phase 1 — Terraform Foundation

Create:

```text
versions.tf
providers.tf
variables.tf
locals.tf
outputs.tf
terraform.tfvars.example
.gitignore
```

Run:

```bash
terraform fmt
terraform init
terraform validate
```

Teach every important block.

---

## Phase 2 — Storage and Database

Create:

```text
S3 buckets
DynamoDB tables
```

Teach:

```text
resource blocks
references
plan
apply
outputs
state
```

---

## Phase 3 — Random and Local Providers

Add:

```text
random
local
```

Generate unique local names and a generated configuration file.

---

## Phase 4 — Messaging

Create:

```text
SQS
DLQ
SNS
subscriptions
```

Teach:

```text
ARN
URL
jsonencode
dependencies
```

---

## Phase 5 — Configuration and Secrets

Create:

```text
SSM
Secrets Manager
KMS
```

Teach state security and sensitive values.

---

## Phase 6 — IAM

Create Lambda execution permissions.

Teach:

```text
roles
policies
attachments
assume-role policy
```

---

## Phase 7 — Lambda

Create:

```text
create_order
process_order
```

Use Python.

Package with the Archive provider.

---

## Phase 8 — API Gateway

Create API -> Lambda integration where supported.

---

## Phase 9 — Events

Introduce EventBridge and event-driven integrations where supported.

---

## Phase 10 — Advanced Terraform

Practice:

```text
for_each
count
conditionals
functions
templates
lifecycle
depends_on
terraform console
terraform graph
```

---

## Phase 11 — State Operations

Practice:

```text
state list
state show
replace
import
drift detection
```

---

## Phase 12 — Modules

Refactor suitable infrastructure into modules.

Do not change architecture unnecessarily.

---

## Phase 13 — Destroy

Run:

```bash
terraform plan -destroy
terraform destroy
```

Before applying destroy, explain Terraform's dependency-based destruction order.

Verify resources have been removed from Floci.

---

# 19. AWS CLI Verification

After creating each AWS service, show a matching verification command.

Use:

```bash
--endpoint-url http://localhost:4566
```

Examples:

```bash
aws --endpoint-url http://localhost:4566 s3api list-buckets

aws --endpoint-url http://localhost:4566 dynamodb list-tables

aws --endpoint-url http://localhost:4566 sqs list-queues

aws --endpoint-url http://localhost:4566 sns list-topics

aws --endpoint-url http://localhost:4566 lambda list-functions

aws --endpoint-url http://localhost:4566 ssm describe-parameters
```

Only use commands supported by Floci.

---

# 20. Codex Development Rules

Codex should act as both:

```text
Terraform engineer
Terraform mentor
```

For every phase:

1. Explain what will be created.
2. Explain why it is useful.
3. Implement it.
4. Run formatting where possible.
5. Run validation.
6. Show the Terraform plan.
7. Explain important plan lines.
8. Apply only when appropriate.
9. Verify using AWS CLI against Floci.
10. Inspect Terraform state.
11. Give the user one small exercise.

When Codex writes Terraform such as:

```hcl
resource "aws_s3_bucket" "assets" {
  bucket = "${local.name_prefix}-${random_id.suffix.hex}"
}
```

explain:

```text
resource
aws_s3_bucket
assets
bucket
local.name_prefix
random_id.suffix.hex
```

Also explain the resulting resource address:

```text
aws_s3_bucket.assets
```

---

# 21. Safety / Restrictions

Do not:

- Connect to real AWS.
- Ask for real AWS credentials.
- Create billable AWS infrastructure.
- Commit secrets.
- Hardcode personal credentials.
- Manually modify Terraform state.
- Create meaningless resources only to reach a count.
- Hide the project behind modules immediately.
- Run destructive commands without first showing the plan.
- Assume a Floci feature is supported without verification when uncertain.

---

# 22. MVP Acceptance Criteria

The MVP is complete when all applicable conditions below are met.

- Floci runs locally.
- Terraform initializes successfully.
- AWS provider talks to Floci.
- Random provider is used.
- Local provider is used.
- Archive provider is used.
- At least 20 meaningful resources are managed by Terraform.
- S3 resources exist.
- DynamoDB resources exist.
- SQS resources exist.
- SNS resources exist.
- IAM resources exist.
- Lambda functions exist.
- SSM parameters exist.
- Secrets Manager is demonstrated.
- KMS is demonstrated where supported.
- CloudWatch log groups are demonstrated where supported.
- EventBridge/API Gateway are demonstrated where supported.
- Terraform variables are used.
- Terraform locals are used.
- Terraform outputs are used.
- `for_each` is demonstrated.
- `count` is demonstrated.
- Conditional expressions are demonstrated.
- Terraform functions are demonstrated.
- A data source is demonstrated.
- `templatefile()` is demonstrated.
- State inspection is demonstrated.
- Drift is demonstrated.
- Import is demonstrated.
- `-replace` is demonstrated.
- `terraform console` is demonstrated.
- `terraform graph` is demonstrated.
- At least one component is later refactored into a module.
- `terraform destroy` successfully cleans the environment.
- README contains setup, architecture, usage, verification, and cleanup instructions.

---

# 23. Definition of Done

The project must support this learning workflow:

```bash
terraform init

terraform fmt -recursive

terraform validate

terraform plan

terraform apply

terraform state list

terraform output

terraform destroy
```

The learner should understand not only **how to run these commands**, but also:

```text
what Terraform is doing
why it is doing it
how Terraform knows resource order
where Terraform stores state
how Terraform detects changes
how resources reference one another
how providers communicate with APIs
how reusable modules are constructed
```

---

# 24. Codex Starting Instruction

When Codex receives this file, begin with **Phase 0 only**.

Do not generate the complete project immediately.

Phase 0 should:

1. Inspect the existing repository.
2. Check Terraform installation.
3. Check Docker installation.
4. Check Docker Compose installation.
5. Check AWS CLI installation.
6. Determine whether Floci is already running.
7. Create the minimum required Floci startup configuration if necessary.
8. Start Floci.
9. Verify `localhost:4566`.
10. Verify AWS CLI communication with Floci.
11. Summarize the final architecture and expected resource groups.

Stop after Phase 0 unless the user explicitly asks to continue.

The purpose of this repository is **learning Terraform by building**, not merely generating Terraform files.
