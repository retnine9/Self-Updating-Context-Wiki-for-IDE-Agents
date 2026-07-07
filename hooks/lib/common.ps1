# Shared helpers for context wiki hooks

function Get-RepoRoot {
    # hooks/lib -> repo root
    $libDir = Split-Path -Parent $PSScriptRoot
    return Split-Path -Parent $libDir
}

function Get-Python {
    if ($env:WIKI_PYTHON) { return $env:WIKI_PYTHON }
    $py = Get-Command python -ErrorAction SilentlyContinue
    if ($py) { return $py.Source }
    return "python"
}

function Get-ContextDir {
    if ($env:CONTEXT_WIKI_DIR) { return $env:CONTEXT_WIKI_DIR }
    return Join-Path $env:USERPROFILE ".cursor\context"
}

function Write-WikiLog {
    param([string]$Message)
    $ctx = Get-ContextDir
    $log = Join-Path $ctx "wiki.log"
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    try {
        New-Item -ItemType Directory -Force -Path $ctx | Out-Null
        Add-Content -Path $log -Value "[$ts] hook: $Message" -ErrorAction SilentlyContinue
    } catch {}
}
