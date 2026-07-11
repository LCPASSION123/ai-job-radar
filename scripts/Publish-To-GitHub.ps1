param(
    [string]$RepoName = "ai-job-radar",
    [switch]$Private
)

$ErrorActionPreference = "Stop"
$root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $root

$machinePath = [Environment]::GetEnvironmentVariable("Path", "Machine")
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
$env:Path = "$machinePath;$userPath"

if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    throw "GitHub CLI is not installed. Install it with: winget install --id GitHub.cli --source winget"
}

if (-not (Test-Path ".git")) {
    git init -b main
}

$status = git status --porcelain
if ($status) {
    throw "Working tree is not clean. Commit or stash changes before publishing."
}

gh auth status *> $null
if ($LASTEXITCODE -ne 0) {
    gh auth login --hostname github.com --git-protocol https --web
}

$description = "Local-first AI freelance job radar with FastAPI, React, MCP, imports, scoring, and proposal drafts."
$visibility = if ($Private) { "--private" } else { "--public" }

$origin = git remote get-url origin 2>$null
if ($LASTEXITCODE -eq 0 -and $origin) {
    git push -u origin main
} else {
    gh repo create $RepoName $visibility --description $description --source . --remote origin --push
}

gh repo view --web
