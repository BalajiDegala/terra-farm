# Changelog

## 0.1.0 — MVP

- Fifteen sequential runbooks, from machine setup through Terraform cleanup.
- Local order-processing infrastructure using Floci, four Terraform providers, and 36 managed
  resources; the import exercise adds a 37th resource.
- Working Lambda/API order flow, SNS notifications, and EventBridge audit delivery.
- Exercises for expressions, state, drift, import, replacement, module migration, and an optional
  versioned S3 backend with locking.
- Locked provider selections, portable Python helpers, and PowerShell-compatible commands.
- Platform-specific Terraform selection and Linux-compatible release checksums, including ZIPs built on Windows.
- Provider package hashes for Windows AMD64 and Linux/macOS AMD64 and ARM64.
- Maintained source checks, an isolated integration runner, and CI configurations for three operating systems.
- Full-course execution verified on Windows and Ubuntu/WSL2 with Docker Desktop, including backend locking and cleanup.
- A source-only release ZIP and SHA256 manifest for learners without Git access.

See [validation](runbooks/validation.md) for executed checks and platform limits, and
[MVP acceptance](runbooks/acceptance.md) for the requirement-to-chapter mapping.
