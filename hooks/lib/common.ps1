# Shared helpers for context wiki hooks

function Import-WikiEnv {
    $envFile = Join-Path $env:USERPROFILE ".cursor\wiki\wiki.env"
    if (-not (Test-Path $envFile)) { return }
    Get-Content $envFile -ErrorAction SilentlyContinue | ForEach-Object {
        if ($_ -match '^\s*([^#=]+)=(.*)$') {
            $key = $matches[1].Trim()
            $val = $matches[2].Trim().Trim('"').Trim("'")
            if ($key) { Set-Item -Path "env:$key" -Value $val }
        }
    }
}

function Get-WikiHome {
    Import-WikiEnv
    if ($env:WIKI_HOME) { return $env:WIKI_HOME }
    $installed = Join-Path $env:USERPROFILE ".cursor\wiki"
    if (Test-Path (Join-Path $installed "install.json")) { return $installed }
    # Dev fallback: hooks/lib -> repo root
    $libDir = Split-Path -Parent $PSScriptRoot
    return (Split-Path -Parent $libDir)
}

function Get-Python {
    Import-WikiEnv
    if ($env:WIKI_PYTHON) { return $env:WIKI_PYTHON }
    foreach ($cmd in @("py", "python3", "python")) {
        $found = Get-Command $cmd -ErrorAction SilentlyContinue
        if ($found) {
            if ($cmd -eq "py") { return "py -3" }
            return $found.Source
        }
    }
    return "python"
}

function Invoke-WikiPython {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Args)
    $python = Get-Python
    if ($python -match '\s') {
        $parts = $python -split '\s+'
        & $parts[0] @($parts[1..($parts.Length - 1)] + $Args)
    } else {
        & $python @Args
    }
}

function Get-ContextDir {
    Import-WikiEnv
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
