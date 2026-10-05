# MVP acceptance — 0.1.0

[Course index](../README.md) · [Validation record](validation.md) · [Maintainer commands](maintaining.md)

This maps the acceptance criteria in [MVP.md](../MVP.md#22-mvp-acceptance-criteria) to the delivered
workshop. Learners create resources progressively on their own machine, retain one Terraform state,
and finish with cleanup. The default stack has 36 managed resources; import brings it to 37.

## Infrastructure and workload

| MVP requirement | Delivered lesson and evidence |
| --- | --- |
| Local Floci; Terraform initializes; AWS provider talks to Floci | [00 setup](00-setup.md) and [01 foundation](01-foundation.md): local STS identity and converged output-only plan |
| At least 20 meaningful resources | [09 events](09-events.md): 36 managed resources verified by the integration runner |
| S3 and DynamoDB | [02 storage/database](02-storage-database.md): two buckets and two tables |
| Random and Local providers | [03 generated configuration](03-random-local.md): stable application ID and resource-derived JSON |
| SQS and SNS | [04 messaging](04-messaging.md): orders/DLQ/notification queues, topics, subscription, and queue policy |
| SSM, Secrets Manager, KMS | [05 settings and secrets](05-configuration-secrets.md): parameters, fake secret/version, key/alias, and sensitive-state explanation |
| IAM | [06 permissions](06-iam.md): execution role, policy, and attachment |
| Lambda, Archive provider, CloudWatch logs | [07 functions](07-lambda.md): packaged handlers, log groups, event-source mapping, and complete order smoke check |
| API Gateway | [08 API](08-api.md): HTTP 202 followed by processed order, archive object, and notification |
| EventBridge | [09 events](09-events.md): matching audit event delivered to SQS |
| Cleanup | [14 destroy](14-cleanup.md): reviewed 37-resource destroy, optional two-resource backend destroy, and empty managed state |

## Terraform learning requirements

| MVP requirement | Delivered lesson |
| --- | --- |
| Variables, validation, tfvars, locals, outputs, provider constraints | [01 foundation](01-foundation.md) |
| Resource addresses, references, state inspection, dependency order | [02 resources](02-storage-database.md), [04 messaging](04-messaging.md), [10 graph](10-expressions.md) |
| `templatefile()` and generated configuration | [03 templates](03-random-local.md) |
| `count`, conditionals, `jsonencode()`, `try()` | [04 messaging](04-messaging.md), [07 functions](07-lambda.md), [10 expressions](10-expressions.md) |
| `for_each`, sensitive values, types, maps | [05 settings](05-configuration-secrets.md), [07 functions](07-lambda.md) |
| Data sources and implicit/explicit dependencies | [01 identity](01-foundation.md), [06 IAM](06-iam.md), [07 archives](07-lambda.md) |
| Lifecycle, `terraform console`, `terraform graph`, remaining required functions | [08 deployment](08-api.md), [10 expressions](10-expressions.md) |
| Drift, import, replacement | [11 state exercises](11-state.md) |
| Later module refactor with inputs, outputs, and preserved resources | [12 storage module](12-modules.md) |
| Optional S3 backend, bootstrap problem, locking, historical DynamoDB locking | [13 remote state](13-remote-state.md) |
| `init`, `fmt`, `validate`, reviewed `plan`/`apply`, outputs, and destroy | Repeated throughout the chapters, ending with [14 cleanup](14-cleanup.md) |
| README with setup, architecture, usage, verification, cleanup | [README](../README.md), its course index, and the linked runbooks |

## Delivery and scope

- Every numbered chapter includes an exercise, verification/checkpoint, and troubleshooting guidance.
- Reference source, provider locks, helpers, tests, workflow, and runbooks are included in the release ZIP.
- `.gitignore` excludes state, plans, personal tfvars, generated data, author work, and downloaded tools.
- Automated checks assemble the actual incremental examples; integration checks use uniquely named
  local resources and saved plans. See [maintaining](maintaining.md) to reproduce them.
- The full application is an infrastructure teaching workload. Authentication, payment integration,
  transactional messaging, and production deployment are outside this MVP.
- Windows and Ubuntu/WSL2 have full-course execution evidence, including order processing, state
  exercises, backend locking, and cleanup. macOS and Linux with Docker Engine installed directly,
  plus independent learner feedback, remain follow-up validation, not missing MVP lessons or functionality.
  [GitHub Actions](https://github.com/BalajiDegala/terra-farm/actions) provides ongoing platform checks.

Cleanup may leave an emulator-managed Lambda runtime bucket and KMS keys awaiting their scheduled
deletion window. The requirement is removal of the workshop's managed application/backend resources,
not erasure of the Docker volume or unrelated local infrastructure.
