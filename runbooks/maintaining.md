# Maintaining and distributing the workshop

[Course index](../README.md) · [MVP acceptance](acceptance.md) · [Validation record](validation.md)

Learners start at Chapter 00. The commands here are for authors changing the course or preparing
a new release. Run them from the repository root using Python 3.10+.

## Check a change without provisioning

```text
python scripts/check_workshop.py
```

This checks chapter presence, local documentation links, command quoting, Python syntax, regression
tests, and Terraform formatting. It then assembles Chapters 01–12 in a temporary project, validates
each cumulative configuration, and validates the separately locked backend bootstrap. On Windows
it also checks the saved-plan syntax through Windows PowerShell. It never runs an infrastructure apply.

Terraform is resolved from the project-local install or PATH; override it with `--terraform` if needed.
The first run downloads the locked providers. `--plugin-dir` accepts an existing provider mirror for
offline checks. For documentation/Python work without Terraform, use:

```text
python scripts/check_workshop.py --skip-terraform
```

Success removes the disposable check directory. Failure keeps it under `.workshop/check-...` for inspection.
The learner's `lab/` is not used by these checks.

When updating providers, refresh the locks in `examples/01`, `examples/03`, `examples/07`, and
`examples/13-bootstrap` for every supported platform. From each directory, run:

```text
terraform providers lock -platform=windows_amd64 -platform=linux_amd64 -platform=linux_arm64 -platform=darwin_amd64 -platform=darwin_arm64
```

Review the selected versions and signing information, then commit the updated locks together.
The checker uses read-only locks; Windows-only unpacked-package hashes can make validation fail on
Linux even when initialization downloads the correct signed archive. See HashiCorp's
[cross-platform provider locking instructions](https://developer.hashicorp.com/terraform/cli/commands/providers/lock).

## Verify the complete local course

Install the Chapter 00 prerequisites and start the emulator with Lambda support:

```text
docker compose -f compose.yaml -f compose.lambda.yaml up -d --wait floci
docker pull public.ecr.aws/lambda/python:3.12
python scripts/test_integration.py --run
```

The explicit `--run` selects the integration exercise. It creates a project with a unique
`workshop-ci-...` prefix and a unique backend bucket. It prints planned resource actions, applies the
saved plans, checks clean follow-up plans and managed resource counts, and verifies the order/event flows.
It also exercises console/graph, drift, import, replacement, module moves, backend migration, and lock
contention. Cleanup verifies a 37-resource application destroy and a two-resource backend destroy.
Service listings must also be free of that run's prefix after destruction.
For the known archive cleanup issue, it clears only that run's disposable archive objects after
reviewing the destroy plan. It leaves the emulator available for other work.

If a check fails, it exits nonzero and preserves the test project under `.workshop/integration-...`.
Keep Floci running. Use the printed project path and Chapter 14 to clean it up; a failed remote-state
exercise may first need Chapter 13's migration back to local. Do not remove the directory while it
still owns resources. The integration runner starts a fresh run each time; it does not resume failed runs.

## Continuous integration

[The workflow](../.github/workflows/validate.yml) runs source/chapter checks on Windows, macOS, and
Linux, then the complete Floci integration on a Linux runner. It uses the version in `.terraform-version`
and the checked-in provider locks. No AWS account, real keys, or repository secrets are required.
Checks run on pushes, pull requests, and manual workflow dispatch after this repository is hosted on GitHub.
The workflow being present does not mean its hosted jobs have already run; consult the validation record.

The actions follow the official [checkout](https://github.com/actions/checkout),
[setup-python](https://github.com/actions/setup-python), and
[setup-terraform](https://github.com/hashicorp/setup-terraform) usage. Terraform's wrapper is disabled
so Python receives the CLI's ordinary exit codes and JSON output.

## Build the learner download

Update `VERSION` and `CHANGELOG.md`, complete the checks, then:

```text
python scripts/package_workshop.py
```

For 0.1.0 this writes `dist/terraform-floci-lab-0.1.0.zip` and its `.zip.sha256` checksum.
The ZIP contains one top-level source directory plus `MANIFEST.sha256` with each source file's hash.
On Linux, run `sha256sum --check terraform-floci-lab-0.1.0.zip.sha256` next to the download,
then `sha256sum --check MANIFEST.sha256` inside the extracted directory to verify its contents.
Packaging uses explicit source directories/file types, including hidden provider locks. Learner labs,
Terraform state/plans, generated output, downloaded tools, caches, and author logs are excluded.
Open the ZIP and start with its README after extraction. Learners still download the prerequisites,
providers, and container images during setup.

Before sharing a new version, extract the ZIP into an empty directory and run
`python scripts/check_workshop.py --skip-terraform` there. Complete a full course run when changing HCL,
providers, the emulator, or handlers. This package command prepares files locally; it does not publish
to a hosting service or create a GitHub release.
