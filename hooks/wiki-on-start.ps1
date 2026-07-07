# wiki-on-start.ps1 -- sessionStart: extract new transcripts + prepare synthesis
param()

$ErrorActionPreference = "SilentlyContinue"
. "$PSScriptRoot\lib\common.ps1"

$repo = Get-RepoRoot
$python = Get-Python
$ctx = Get-ContextDir
$skipFile = Join-Path $ctx ".wiki_skip"

if (Test-Path $skipFile) {
    Write-WikiLog "sessionStart skipped (.wiki_skip exists)"
    Remove-Item $skipFile -Force -ErrorAction SilentlyContinue
    Write-Output "{}"
    exit 0
}

$env:CONTEXT_WIKI_DIR = $ctx
Write-WikiLog "sessionStart: update_wiki.py --all"
try {
    $out = & $python "$repo\scripts\update_wiki.py" --all 2>&1
    Write-WikiLog "sessionStart result: $out"
} catch {
    Write-WikiLog "sessionStart ERROR: $_"
}

Write-Output "{}"
exit 0
