# inject-wiki-drain.ps1 -- beforeSubmitPrompt: mandate synthesis on first message
param()

$ErrorActionPreference = "SilentlyContinue"
. "$PSScriptRoot\lib\common.ps1"

$ctx = Get-ContextDir
$drainFile = Join-Path $ctx ".drain_required.json"
$injectedFile = Join-Path $ctx ".drain_injected"

if (-not (Test-Path $drainFile)) {
    Write-Output "{}"
    exit 0
}

# One-shot per session
if (Test-Path $injectedFile) {
    Write-Output "{}"
    exit 0
}

try {
    $drain = Get-Content $drainFile -Raw | ConvertFrom-Json
    $count = $drain.count
} catch {
    Write-Output "{}"
    exit 0
}

$repo = Get-RepoRoot
$msg = @"
MANDATORY CONTEXT WIKI DRAIN: $count session(s) need synthesis before you address the user's request.

1. Run: python "$repo\scripts\update_wiki.py" --manifest
2. For each layer2_batches entry, write extracts to extract_path (spawn subagents in batches of 10 if many).
3. Update all six layer3_files per layer3_instruction (complete file replacements).
4. Run: python "$repo\scripts\update_wiki.py" --complete

Use only facts from session transcripts. Then proceed with the user's actual request.
If the user said to skip wiki update, run --complete and delete .drain_required.json instead.
"@

New-Item -ItemType File -Force -Path $injectedFile | Out-Null

$response = @{
    agent_message = $msg
} | ConvertTo-Json -Compress

Write-Output $response
exit 0
