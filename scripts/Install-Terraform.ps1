# Downloads the pinned Windows CLI into this project; no admin install or global PATH change.
[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$labRoot = Split-Path -Parent $PSScriptRoot
$version = (Get-Content -LiteralPath (Join-Path $labRoot '.terraform-version') -Raw).Trim()
if ($version -notmatch '^\d+\.\d+\.\d+$') {
    throw 'Expected a stable Terraform version in .terraform-version.'
}
$architecture = switch ($env:PROCESSOR_ARCHITECTURE) {
    'AMD64' { 'amd64' }
    'ARM64' { 'arm64' }
    default { throw 'This installer supports Windows AMD64 and ARM64.' }
}
$toolDirectory = Join-Path $labRoot '.tools\terraform'
$downloadDirectory = Join-Path $labRoot '.tools\downloads'
New-Item -ItemType Directory -Path $toolDirectory, $downloadDirectory -Force | Out-Null

$archiveName = "terraform_${version}_windows_${architecture}.zip"
$archivePath = Join-Path $downloadDirectory $archiveName
$checksumPath = Join-Path $downloadDirectory "terraform_${version}_SHA256SUMS"
$releaseUrl = "https://releases.hashicorp.com/terraform/$version"

[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
Invoke-WebRequest -UseBasicParsing -Uri "$releaseUrl/$archiveName" -OutFile $archivePath -TimeoutSec 120
Invoke-WebRequest -UseBasicParsing -Uri "$releaseUrl/terraform_${version}_SHA256SUMS" -OutFile $checksumPath -TimeoutSec 30

$checksumPattern = '^([a-fA-F0-9]{64})\s+' + [regex]::Escape($archiveName) + '$'
$expectedHash = $null
foreach ($line in Get-Content -LiteralPath $checksumPath) {
    if ($line -match $checksumPattern) { $expectedHash = $Matches[1] }
}
if (-not $expectedHash) { throw "No published checksum found for $archiveName." }
$actualHash = (Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash
if ($actualHash -ne $expectedHash) { throw 'Terraform archive checksum mismatch; installation stopped.' }

Expand-Archive -LiteralPath $archivePath -DestinationPath $toolDirectory -Force
Write-Host 'Verified archive SHA256 against the HashiCorp HTTPS release manifest.'
& (Join-Path $toolDirectory 'terraform.exe') version
if ($LASTEXITCODE -ne 0) { throw 'Terraform version check failed.' }
Write-Host 'Installed locally. Run: . .\scripts\Use-LocalLab.ps1'
