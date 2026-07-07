# inject-wiki-drain.ps1 -- beforeSubmitPrompt: mandate synthesis on first message
param()

$ErrorActionPreference = "SilentlyContinue"
. "$PSScriptRoot\lib\common.ps1"

$wikiHome = Get-WikiHome
$ctx = Get-ContextDir
$drainFile = Join-Path $ctx ".drain_required.json"
$injectedFile = Join-Path $ctx ".drain_injected"

if (-not (Test-Path $drainFile)) {
    Write-Output "{}"
    exit 0
}

if (Test-Path $injectedFile) {
    Write-Output "{}"
    exit 0
}

try {
    $null = Get-Content $drainFile -Raw | ConvertFrom-Json
} catch {
    Write-Output "{}"
    exit 0
}

$env:CONTEXT_WIKI_DIR = $ctx
$env:WIKI_HOME = $wikiHome
$json = Invoke-WikiPython "$wikiHome\scripts\update_wiki.py" --drain-message 2>&1
if (-not $json -or $json -eq "{}") {
    Write-Output "{}"
    exit 0
}

New-Item -ItemType File -Force -Path $injectedFile | Out-Null
Write-Output $json
exit 0
