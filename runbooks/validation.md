# Validation and compatibility record

[Course index](../README.md) · [MVP acceptance](acceptance.md) · [Reproduce the checks](maintaining.md)

This record distinguishes executed checks from configured CI and guidance for other machines.

## MVP 0.1.0 reference environment

- Windows host with Docker Desktop's Linux engine, Terraform 1.16.5, Floci 2.1.0, and AWS CLI 2.36.19.
- Ubuntu 22.04.3 LTS on WSL2, using native Linux AMD64 Terraform 1.16.5 and AWS CLI 2.36.19,
  Docker Desktop's Linux engine 29.1.3, and Compose 2.40.3-desktop.1. The source ZIP was extracted
  onto the Linux filesystem; Windows executables and learner state were not reused.
- AWS provider 6.67.0, Random 3.9.1, Local 2.9.1, and Archive 2.8.1 from the supplied dependency locks.
- Windows Python 3.11 and Ubuntu Python 3.10.12 for the seven regression tests.
- Seven regression tests cover learner state/tfvars preservation, source backups, chapter ordering and
  missing sources, local credential/endpoint isolation, malformed order inputs, partial-batch retry
  reporting, platform-specific Terraform selection, and release packaging that excludes learner state
  while retaining provider locks and writing Linux-compatible checksums.

## Executed checks

| Check | Result |
| --- | --- |
| Chapter content, local links, Python syntax, regression tests | Passed on Windows and Ubuntu 22.04 under WSL2 |
| Terraform formatting and validation | All 12 cumulative chapter configurations and the separately locked bootstrap passed on Windows and Ubuntu/WSL2 |
| Native Windows PowerShell saved-plan syntax | Passed with quoted whole-option arguments |
| Compose base plus Lambda override | Configuration accepted; emulator healthy |
| GitHub Actions workflow syntax | Passed actionlint 1.7.12 |
| Windows-built source ZIP on Linux | ZIP checksum and all 80 source-file hashes passed `sha256sum --check` |
| Full local integration with the maintained runner | Passed on Windows and Ubuntu/WSL2: order/event flows, state exercises, backend migration/locking, and all 39 managed application/backend resources destroyed |

The final MVP integration run verified Chapters 01–09 in order, expected resource counts,
clean follow-up plans, SNS delivery, Lambda/API processing, S3 archival, and EventBridge audit delivery.
It also verified drift repair, SSM import, file replacement, storage module moves without replacement,
S3 backend migration, actual lock contention, migration back to local, and application/backend cleanup.
The Ubuntu/WSL2 run on 2026-10-05 used project `workshop-ci-03f14b05`, passed every integration check,
and verified that service listings contained no entries with its test prefix after cleanup.

The maintained runner repeats those checks with a unique project prefix and a unique backend bucket.
It prints saved-plan actions, verifies resource counts and convergence, and preserves source/state on
failure. A successful run removes its 37 application resources and two backend resources, then removes
its disposable workspace. [Maintainer instructions](maintaining.md) document the exact commands.

## Review corrections included in this release

- PowerShell requires quotes around arguments such as `"-out=build/chapter01.tfplan"` in the provided
  commands. The first author driver used Python subprocesses and missed that shell parsing issue;
  the maintained checker now also invokes Windows PowerShell directly.
- The local AWS wrapper rejects abbreviated endpoint/profile overrides as well as full flag names.
- The chapter copier stops if a required reference directory is missing, preserving its progress marker.
- The separate backend bootstrap includes its own AWS provider lock file.
- Provider locks include unpacked-package hashes for Windows AMD64 and Linux/macOS AMD64 and ARM64.
  The initial Windows-only hashes failed Linux validation with read-only locks; the hashes were refreshed
  using signed registry packages without changing provider versions.
- Workload helpers select the current platform's Terraform executable, including when a checkout
  contains a Windows executable and is opened in WSL.
- Release checksum files use LF on every build platform so Linux `sha256sum --check` accepts Windows-built ZIPs.
- The OpenAPI accepted response is HTTP 202, matching the handler and smoke checks.
- Archive deletion sometimes kept retrying with old test objects despite `force_destroy` in the
  reference emulator/provider combination. [Chapter 14](14-cleanup.md#if-archive-bucket-deletion-keeps-retrying)
  documents the observed recovery; the integration runner clears only its own test archive before
  applying the reviewed destroy plan. Versioned backend cleanup passed through Terraform.

## CI and platform scope

[The provided workflow](../.github/workflows/validate.yml) runs source/chapter validation on Windows,
macOS, and Linux and full integration on Linux. It has been syntax-checked locally. The table above
records local execution; hosted run results are tracked in
[GitHub Actions](https://github.com/BalajiDegala/terra-farm/actions).
The versioned ZIP can be distributed and used independently of GitHub.

The full course has execution evidence on Windows and Ubuntu/WSL2 using Docker Desktop's Linux engine.
The Ubuntu run used native Linux CLI binaries on a fresh source extraction and exercised Docker socket
access and Lambda networking. Linux with Docker Engine installed directly, and macOS including Apple
silicon, remain follow-up host validation. Their package hashes are present in the provider locks;
that alone does not constitute an executed course run. A new learner trial is also useful for improving
explanations. These are platform/usability follow-ups, not missing course chapters.

## Known limits

- Floci 2.1.0 and AWS provider 6.67.0 have tag read-back mismatches on Lambda event-source mappings
  and API Gateway stages. Chapters 07–08 use the explicitly local `aws.untagged` alias for those two
  resources; other resources retain their default tags.
- The emulator does not prove real AWS IAM enforcement, quotas, durability, billing, or availability.
- Secret generation and KMS are separate configuration lessons. Handlers use fake credentials and
  local endpoints; the order workflow has no real payment integration.
- Database/queue writes are non-atomic and messages may be delivered more than once. Production use
  would need authentication, reconciliation, and deliberate idempotency for external effects.
- Destroy can schedule KMS deletion rather than immediately erasing the key. Floci may retain its own
  Lambda runtime bucket; application cleanup does not erase unrelated emulator data.

Service references: [Lambda](https://floci.io/floci/services/lambda/),
[API Gateway](https://floci.io/floci/services/api-gateway/),
[EventBridge](https://floci.io/floci/services/eventbridge/),
[KMS](https://floci.io/floci/services/kms/).
