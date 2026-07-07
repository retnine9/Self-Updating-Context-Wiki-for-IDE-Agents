# Optional shortcut — same steps as docs/SETUP.md
# Installs context wiki runtime to ~/.cursor/wiki/
param(
    [string]$RepoRoot = (Split-Path -Parent $PSScriptRoot)
)

$ErrorActionPreference = "Stop"
Write-Host "Context Wiki install (optional shortcut — see docs/SETUP.md)"
Write-Host "Source: $RepoRoot"

$installer = Join-Path $RepoRoot "scripts\install_wiki.py"
if (-not (Test-Path $installer)) {
    Write-Error "Missing $installer — clone the full repository first."
}

# Find Python
$python = $null
foreach ($cmd in @("py", "python3", "python")) {
    $found = Get-Command $cmd -ErrorAction SilentlyContinue
    if ($found) {
        if ($cmd -eq "py") { $python = "py -3" } else { $python = $found.Source }
        break
    }
}
if (-not $python) {
    $localPy = Get-ChildItem "$env:LOCALAPPDATA\Python\pythoncore-*\python.exe" -ErrorAction SilentlyContinue |
        Sort-Object FullName -Descending | Select-Object -First 1
    if ($localPy) { $python = $localPy.FullName }
}
if (-not $python) {
    Write-Error "Python 3 not found. Install Python 3 and retry, or follow docs/SETUP.md step 2."
}

Write-Host "Using Python: $python"
if ($python -match '\s') {
    $parts = $python -split '\s+'
    & $parts[0] $parts[1] $installer --source-repo $RepoRoot
} else {
    & $python $installer --source-repo $RepoRoot
}

if ($LASTEXITCODE -ne 0 -and $LASTEXITCODE -ne 1) {
    Write-Error "Install failed (exit $LASTEXITCODE). See docs/TROUBLESHOOTING.md"
}

Write-Host "Done. Restart Cursor."
