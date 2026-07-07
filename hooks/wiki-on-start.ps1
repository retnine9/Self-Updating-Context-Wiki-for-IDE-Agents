# wiki-on-start.ps1 -- sessionStart: extract new transcripts + prepare synthesis
param()

$ErrorActionPreference = "SilentlyContinue"
. "$PSScriptRoot\lib\common.ps1"

$wikiHome = Get-WikiHome
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
$env:WIKI_HOME = $wikiHome
Write-WikiLog "sessionStart: update_wiki.py --all (wiki=$wikiHome)"
try {
    $out = Invoke-WikiPython "$wikiHome\scripts\update_wiki.py" --all 2>&1
    Write-WikiLog "sessionStart result: $out"
} catch {
    Write-WikiLog "sessionStart ERROR: $_"
}

Write-Output "{}"
exit 0
