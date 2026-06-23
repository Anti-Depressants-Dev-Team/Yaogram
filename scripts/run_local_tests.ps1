param(
    [switch]$Build,
    [switch]$VerifyBuild,
    [string]$Config = "Debug"
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$Runner = Join-Path $RepoRoot "scripts\run_local_tests.py"

$Arguments = @()
if ($Build) {
    $Arguments += "--build"
}
if ($VerifyBuild) {
    $Arguments += "--verify-build"
}
if ($Config -ne "Debug") {
    $Arguments += @("--config", $Config)
}

& python $Runner @Arguments
exit $LASTEXITCODE
