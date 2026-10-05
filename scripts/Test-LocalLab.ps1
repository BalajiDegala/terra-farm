[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$labRoot = Split-Path -Parent $PSScriptRoot

function Invoke-LabCheck {
    param([string]$Program, [string[]]$Arguments)
    & $Program @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$Program $($Arguments -join ' ') failed with exit code $LASTEXITCODE."
    }
}

# Preserve the caller's shell settings; verification uses only the local lab profile.
$environmentNames = @(
    'AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_SESSION_TOKEN', 'AWS_SECURITY_TOKEN',
    'AWS_PROFILE', 'AWS_DEFAULT_PROFILE', 'AWS_CONFIG_FILE', 'AWS_SHARED_CREDENTIALS_FILE',
    'AWS_DEFAULT_REGION', 'AWS_REGION', 'AWS_ENDPOINT_URL', 'AWS_IGNORE_CONFIGURED_ENDPOINT_URLS',
    'AWS_EC2_METADATA_DISABLED', 'AWS_CLI_AUTO_PROMPT', 'AWS_PAGER', 'PATH'
)
$previousEnvironment = @{}
foreach ($name in $environmentNames) {
    $previousEnvironment[$name] = [Environment]::GetEnvironmentVariable($name, 'Process')
}

try {
    . (Join-Path $PSScriptRoot 'Use-LocalLab.ps1')
    Invoke-LabCheck 'terraform' @('version')
    Invoke-LabCheck 'docker' @('--version')
    Invoke-LabCheck 'docker' @('compose', 'version')
    Invoke-LabCheck 'docker' @('compose', '-f', (Join-Path $labRoot 'compose.yaml'), 'config', '--quiet')
    Invoke-LabCheck 'docker' @('compose', '-f', (Join-Path $labRoot 'compose.yaml'), 'ps')
    Invoke-LabCheck 'aws' @('--version')

    # S3 ListBuckets also checks HTTP reachability without creating a bucket.
    Invoke-LabCheck 'curl.exe' @('--fail', '--silent', '--show-error', '--max-time', '10', 'http://localhost:4566')
    $awsOptions = @('--endpoint-url', 'http://localhost:4566', '--region', 'us-east-1',
        '--no-cli-pager', '--output', 'json', '--cli-connect-timeout', '5', '--cli-read-timeout', '10')
    Invoke-LabCheck 'aws' ($awsOptions + @('sts', 'get-caller-identity'))
    Invoke-LabCheck 'aws' ($awsOptions + @('s3api', 'list-buckets'))
    Invoke-LabCheck 'aws' ($awsOptions + @('dynamodb', 'list-tables'))
    Invoke-LabCheck 'aws' ($awsOptions + @('sqs', 'list-queues'))
    Write-Host 'Phase 0 checks passed. All AWS requests above used localhost:4566; no application resources were created.'
}
finally {
    foreach ($name in $environmentNames) {
        [Environment]::SetEnvironmentVariable($name, $previousEnvironment[$name], 'Process')
    }
}
