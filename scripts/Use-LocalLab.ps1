# Dot-source this file to configure the CURRENT PowerShell session:
# . .\scripts\Use-LocalLab.ps1
# Close this shell when finished. No user/global AWS files are modified.
$labRoot = Split-Path -Parent $PSScriptRoot
$labAwsConfig = Join-Path $labRoot 'config\aws-local.ini'

$env:AWS_ACCESS_KEY_ID = 'test'
$env:AWS_SECRET_ACCESS_KEY = 'test'
$env:AWS_SESSION_TOKEN = $null
$env:AWS_SECURITY_TOKEN = $null
$env:AWS_PROFILE = 'default'
$env:AWS_DEFAULT_PROFILE = 'default'
$env:AWS_CONFIG_FILE = $labAwsConfig
$env:AWS_SHARED_CREDENTIALS_FILE = $labAwsConfig
$env:AWS_DEFAULT_REGION = 'us-east-1'
$env:AWS_REGION = 'us-east-1'
$env:AWS_ENDPOINT_URL = 'http://localhost:4566'
$env:AWS_IGNORE_CONFIGURED_ENDPOINT_URLS = 'false'
$env:AWS_EC2_METADATA_DISABLED = 'true'
$env:AWS_CLI_AUTO_PROMPT = 'off'
$env:AWS_PAGER = ''

$labTerraformDir = Join-Path $labRoot '.tools\terraform'
if ((Test-Path -LiteralPath (Join-Path $labTerraformDir 'terraform.exe')) -and
    ($env:PATH -split ';' -notcontains $labTerraformDir)) {
    $env:PATH = $labTerraformDir + ';' + $env:PATH
}

Write-Host 'Local lab: http://localhost:4566 | us-east-1 | fake test credentials'
