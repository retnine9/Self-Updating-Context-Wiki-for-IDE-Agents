# Install context wiki into ~/.cursor/
param(
    [string]$RepoRoot = (Split-Path -Parent $PSScriptRoot)
)

$ErrorActionPreference = "Stop"
$CursorDir = Join-Path $env:USERPROFILE ".cursor"
$ContextDir = Join-Path $CursorDir "context"
$RulesDir = Join-Path $CursorDir "rules"
$SkillsDir = Join-Path $CursorDir "skills\lint-context"
$HooksFile = Join-Path $CursorDir "hooks.json"

Write-Host "Installing from: $RepoRoot"

# Rules
New-Item -ItemType Directory -Force -Path $RulesDir | Out-Null
Copy-Item "$RepoRoot\cursor\rules\*.mdc" $RulesDir -Force
Write-Host "Rules installed to $RulesDir"

# Skill
New-Item -ItemType Directory -Force -Path $SkillsDir | Out-Null
Copy-Item "$RepoRoot\skills\lint-context\SKILL.md" $SkillsDir -Force
Write-Host "Skill installed to $SkillsDir"

# Context dir from templates
New-Item -ItemType Directory -Force -Path $ContextDir | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $ContextDir "sessions") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $ContextDir "extracts") | Out-Null
$synthDir = Join-Path $ContextDir "synthesis"
New-Item -ItemType Directory -Force -Path $synthDir | Out-Null

foreach ($f in Get-ChildItem "$RepoRoot\templates\synthesis\*.md") {
    $dest = Join-Path $synthDir $f.Name
    if (-not (Test-Path $dest)) {
        Copy-Item $f.FullName $dest
    }
}

if (-not (Test-Path (Join-Path $ContextDir "wiki_config.json"))) {
    Copy-Item "$RepoRoot\templates\wiki_config.example.json" (Join-Path $ContextDir "wiki_config.json")
}
if (-not (Test-Path (Join-Path $ContextDir "wiki_state.json"))) {
    '{"last_extract":null,"last_synthesis":null,"pending_sessions":[]}' | Set-Content (Join-Path $ContextDir "wiki_state.json")
}
if (-not (Test-Path (Join-Path $ContextDir "INDEX.md"))) {
    "# Session Index`n`n*No sessions yet.*`n" | Set-Content (Join-Path $ContextDir "INDEX.md")
}
Write-Host "Context dir initialized at $ContextDir"

# Merge hooks.json
$wikiHooks = @{
    sessionStart = @(@{
        command = "powershell -ExecutionPolicy Bypass -File `"$RepoRoot\hooks\wiki-on-start.ps1`""
        timeout = 120
    })
    beforeSubmitPrompt = @(@{
        command = "powershell -ExecutionPolicy Bypass -File `"$RepoRoot\hooks\inject-wiki-drain.ps1`""
        matcher = "UserPromptSubmit"
        timeout = 15
    })
}

if (Test-Path $HooksFile) {
    $existing = Get-Content $HooksFile -Raw | ConvertFrom-Json
    if (-not $existing.hooks) { $existing | Add-Member -NotePropertyName hooks -NotePropertyValue (@{}) }
    $existing.hooks.sessionStart = $wikiHooks.sessionStart
    $existing.hooks.beforeSubmitPrompt = $wikiHooks.beforeSubmitPrompt
    $existing | ConvertTo-Json -Depth 10 | Set-Content $HooksFile
} else {
    @{ version = 1; hooks = $wikiHooks } | ConvertTo-Json -Depth 10 | Set-Content $HooksFile
}
Write-Host "Hooks merged into $HooksFile"
Write-Host "Done. Restart Cursor."
