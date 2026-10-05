# Troubleshooting and resuming the workshop

[Course index](../README.md)

Start by recording the chapter, exact command, tool versions, and error. Keep state and emulator data.
Avoid sharing state files or secret values when asking for help.

| Symptom | Check and recovery |
| --- | --- |
| `terraform` not found | Install the pinned CLI or add `.tools/terraform` to the current Windows PATH; reopen the shell after system installation. |
| `python` not found on macOS/Linux | Use `python3` in all commands. Python 3.10+ is required. |
| Windows scripts disabled | The optional installer uses a process-scoped execution-policy flag. Core chapter/AWS helpers are Python and do not require PowerShell scripts. |
| PowerShell reports “Too many command line arguments” for a plan | Keep the quotes around the whole option: `terraform plan "-out=build/check.tfplan"`. Quote `"-replace=local_file.app_config"` the same way. |
| PowerShell rejects `curl --fail` | Use `curl.exe --fail http://localhost:4566`; `curl` can be an alias for `Invoke-WebRequest` in Windows PowerShell. |
| Docker cannot connect | Start Docker Desktop/Engine; run `docker info`; on Windows use Linux containers. Check Linux Docker socket permissions through the Docker installation guide. |
| Port 4566 occupied | Stop your other emulator intentionally or use a different machine. This course pins port 4566; do not silently attach to somebody else's resources. |
| CLI works but Terraform fails | Compare region, configured service endpoints, pinned provider version, and Floci logs. Each new AWS service needs its own endpoint entry. |
| Provider install slow/fails | `init` needs registry and HashiCorp release access. Check DNS/proxy/disk space; retry. Keep the lock file; do not disable checksum verification. |
| `lab/` already exists at Chapter 01 | Resume the existing course. Do not delete state to restart; destroy first, then archive the lab. |
| Copier says wrong chapter order | Read `lab/.chapter.json` to see the last copied chapter. Finish its exercises, then copy the next. The marker records file copying, not completion. |
| Copier says reference files are missing | Restore `examples/` from the workshop source. Chapters 10–11 intentionally add no files; other chapters must contain reference files before progress advances. |
| I edited a file that a later chapter replaces | The copier saves the old version under `.workshop/backups/`. Compare it with the new reference and deliberately reapply your exercise changes. |
| No resources shown | Run Terraform from `lab/`, not repository root or an individual `examples/NN/` folder. |
| Objects exist but state is empty | Find the original state/working directory. Multiple checkouts may share the same emulator names. Use the import lesson only when intentionally adopting an object. |
| Unexpected replacement | Stop before apply. Compare names, immutable fields, tfvars, and addresses; changing naming inputs after creation can replace resources. |
| Lambda deploys but does not run | Start with both Compose files. Check Docker socket access and `docker compose logs --tail 100 floci`. Runtime downloads happen on first invocation. |
| First Lambda smoke times out while downloading | Wait for the runtime pull in Floci logs, then rerun smoke; it seeds the same product and creates a fresh order. |
| Lambda cannot reach services | Host clients use localhost; Lambda uses Docker's `floci` service hostname. Verify the default Compose network; remote daemons/rootless setups need separate adaptation. |
| Order stays PENDING | Inspect Lambda logs, event-source mappings, queue/DLQ counts. A DynamoDB write followed by an SQS failure can leave an orphaned row in this teaching workload. |
| Notification missing | Receives hide messages for a visibility timeout. Check the SNS subscription/queue policy and rerun a fresh smoke test after the timeout. |
| API responds 404/502 | Use `terraform output -raw api_endpoint`; inspect API stage/deployment and Lambda logs. |
| Floci operation is unsupported | Record service/operation, image and provider versions. Keep AWS endpoints local. Stay at the previous working checkpoint or skip an explicitly optional exercise. |
| State locked | Check for another apply or console; wait/cancel it normally. Do not force-unlock a live operation. |
| Remote backend unreachable | Start Floci; preserve its volume and bootstrap state. Changing provider endpoints does not repair backend configuration. |
| Destroy fails | Keep the state and emulator. Fix the named error, review a new destroy plan, then retry. |
| Archive bucket deletion keeps retrying | See the [Chapter 14 recovery](14-cleanup.md#if-archive-bucket-deletion-keeps-retrying) for the observed Floci/provider issue with test-order objects. |

## Resume on the same machine

At repository root, start Floci with `docker compose up -d --wait floci` before Chapter 07, or
`docker compose -f compose.yaml -f compose.lambda.yaml up -d --wait floci` from Chapter 07 onward.
Restore your terminal's Terraform PATH if needed, then `cd lab`, `terraform init`, `terraform state list`,
and `terraform plan`. Read the current chapter checkpoint before progressing.

## Move to another machine

A fresh learner starts at Chapter 00. Moving an **unfinished** lab is different: Terraform state and the
matching Floci volume must move together, and an S3 backend also lives in that emulator volume.
Do not copy only `terraform.tfstate` and assume it recreates infrastructure. The simpler learning path
is to finish cleanup on the original machine and rebuild the course on the new one.

## What is and is not portable

HCL, Python helpers, AWS CLI calls, and chapter content avoid personal paths. Docker Desktop on
Windows/macOS and local Linux Docker Engine are the reference layouts. The Windows installer is
optional; use official Terraform installation on macOS/Linux. Native architecture selection belongs
to the tool installers/Docker, not a hardcoded `linux/amd64` Compose setting.
The reference commands use `us-east-1` and one local emulator per machine.
