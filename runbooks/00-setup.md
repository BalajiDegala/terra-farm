# 00 — Set up your machine

[Course index](../README.md) · [Next: foundation](01-foundation.md)

**Goal:** run Floci and make a read-only AWS request. No application resources in this chapter.
**Start:** a machine with internet access for tool/provider/container downloads and a local terminal.

## 1. Install the prerequisites

| Tool | Windows | macOS | Linux |
| --- | --- | --- | --- |
| Git | [Git installer](https://git-scm.com/downloads) | Git installer or Command Line Tools | Distribution Git package |
| Docker + Compose | [Docker Desktop](https://docs.docker.com/desktop/setup/install/windows-install/), Linux containers, WSL 2 backend | [Docker Desktop](https://docs.docker.com/desktop/setup/install/mac-install/), choose Intel or Apple silicon | [Docker Engine](https://docs.docker.com/engine/install/) and [Compose plugin](https://docs.docker.com/compose/install/linux/) |
| Terraform | Project-local installer below | [Official install instructions](https://developer.hashicorp.com/terraform/install), choose Darwin ARM64/AMD64 | Official installer or Linux ARM64/AMD64 ZIP |
| AWS CLI v2 | [Official installer](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) | Official installer | Official installer |
| Python 3.10+ | [Python installer](https://www.python.org/downloads/), enable PATH | Python 3 installer; command is usually `python3` | Distribution Python 3 package |

Reference versions are Terraform **1.16.5** and Floci **2.1.0**. Use a maintained Docker release
with Compose v2 or later. Allow a few GB of free space for providers and Lambda runtime images.
Start Docker and ensure `docker info` works as your normal user. Rootless Docker/Podman and remote
Docker daemons are outside the reference path, especially for Lambda socket access.

## 2. Get the workshop

Clone the repository, or extract the workshop ZIP:

```text
git clone https://github.com/BalajiDegala/terra-farm.git
cd terra-farm
```

The MVP source download is named `terraform-floci-lab-0.1.0.zip`; extract its top-level directory
before running commands. It contains source and runbooks, so install the prerequisites above on
your own machine. It does not include the author's tools, emulator data, or Terraform state.
Open a terminal in the directory containing this README and `compose.yaml`.
Do not assume the author's drive letter or username. Keep this directory for every chapter.
If you used a ZIP and want version control, run `git init -b main` here.

Windows PowerShell, when Terraform is not already installed:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ./scripts/Install-Terraform.ps1
$env:PATH = (Join-Path (Get-Location) '.tools/terraform') + ';' + $env:PATH
```

The installer checks the download's SHA256 against HashiCorp's HTTPS release manifest and installs
only under `.tools/`. PATH changes above last for this shell. Repeat the PATH command after reopening
a terminal. The process-scoped execution-policy option does not change your system policy.
On macOS/Linux, install Terraform on PATH using the official instructions and match `.terraform-version`.
Do not install an AWS account or configure real AWS keys.

## 3. Verify tools

```text
git --version
terraform version
docker --version
docker compose version
docker info
aws --version
python --version
```

Use `python3 --version` and replace `python` with `python3` throughout the course if necessary.
You need Python 3, not Python 2. The helpers use only Python's standard library.
Check that `aws --version` starts with `aws-cli/2`; some Linux distribution packages install v1.
If it reports v1, install AWS CLI v2 using the official installer linked above and check which executable
your shell resolves with `command -v aws` on Linux/macOS or `Get-Command aws` in PowerShell.

When using Ubuntu in WSL2, enable Docker Desktop integration for that distribution and run the course
from its Linux terminal. Install Linux Terraform and AWS CLI v2 inside WSL and extract or clone the
workshop into your Linux home directory. Keep using that terminal and directory for every chapter.

## 4. Start Floci

From the repository root, on all platforms:

```text
docker compose config --quiet
docker compose up -d --wait floci
docker compose ps
```

Expect `healthy` and port `127.0.0.1:4566->4566/tcp`. Compose stores emulator data in the named
`terraform-floci-lab_floci-data` volume. Port 4566 must be free. Do not start multiple copies of
this workshop simultaneously on the same Docker daemon and port.

The `services` block selects the emulator image, `ports` exposes its loopback endpoint, `environment`
selects persistent storage, and `volumes` keeps data when the container stops.

## 5. Verify HTTP and AWS APIs

In Windows PowerShell:

```powershell
curl.exe --fail http://localhost:4566
```

On macOS/Linux:

```text
curl --fail http://localhost:4566
```

Then, on every platform:

```text
python scripts/aws_local.py sts get-caller-identity
python scripts/aws_local.py s3api list-buckets
python scripts/aws_local.py dynamodb list-tables
python scripts/aws_local.py sqs list-queues
```

The root HTTP response is S3-style XML. Expect account `000000000000` and empty bucket/table/queue
lists on a fresh emulator. The wrapper always supplies fake `test` credentials and `--endpoint-url
http://localhost:4566`; it does not modify your personal AWS profile.

**Checkpoint:** versions print, Floci is healthy, and all four AWS calls succeed.
**Exercise:** explain why an empty bucket list is success and why omitting the local endpoint matters.
**If blocked:** check `docker compose logs --tail 50 floci` and [troubleshooting](troubleshooting.md).
**Pause/resume:** `docker compose stop floci`, then `docker compose up -d --wait floci`. Preserve the volume.

Source: [Floci Compose](https://floci.io/floci/configuration/docker-compose/) and
[storage configuration](https://floci.io/floci/configuration/storage/).
