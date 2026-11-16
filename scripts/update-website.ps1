param(
    [string]$RepoPath = (Join-Path $env:USERPROFILE 'Fleng-GitHub'),
    [string]$PatchPath = (Join-Path $PSScriptRoot 'website.patch')
)
$ErrorActionPreference = 'Stop'
$Release = '2026.11.16-web'
$CommitMessage = "fix: publish Fleng website $Release"

function Invoke-Git {
    param([string[]]$GitArgs)
    & git -C $RepoPath @GitArgs
    if ($LASTEXITCODE -ne 0) { throw "Git failed: $($GitArgs -join ' ')" }
}

try {
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) { throw 'Git is required.' }
    $RepoPath = (Resolve-Path -LiteralPath $RepoPath).Path
    if (-not (Test-Path -LiteralPath $PatchPath -PathType Leaf)) { throw 'website.patch is missing. Extract the entire ZIP first.' }
    $PatchPath = (Resolve-Path -LiteralPath $PatchPath).Path
    $origin = (Invoke-Git -GitArgs @('remote', 'get-url', 'origin') | Out-String).Trim()
    if ($origin -notmatch '^(https://github\.com/Fleng-Fly/fleng-fly(?:\.git)?/?|git@github\.com:Fleng-Fly/fleng-fly(?:\.git)?)$') {
        throw 'This is not the Fleng-Fly/fleng-fly checkout. No update applied.'
    }
    $changes = @(Invoke-Git -GitArgs @('status', '--porcelain', '--untracked-files=no'))
    if ($changes.Count -gt 0) { throw 'Tracked files have local changes. Save/commit those changes before updating. Nothing was overwritten.' }

    Invoke-Git -GitArgs @('fetch', 'origin')
    Invoke-Git -GitArgs @('switch', 'main')
    Invoke-Git -GitArgs @('merge', '--ff-only', 'origin/main')
    $head = (Invoke-Git -GitArgs @('rev-parse', 'HEAD') | Out-String).Trim()
    $remoteHead = (Invoke-Git -GitArgs @('rev-parse', 'origin/main') | Out-String).Trim()
    $subject = (Invoke-Git -GitArgs @('log', '-1', '--format=%s') | Out-String).Trim()
    if ($head -ne $remoteHead -and $subject -ne $CommitMessage) {
        throw 'Local main contains other unpublished commits. Review them before publishing.'
    }

    $versionPath = Join-Path $RepoPath 'frontend/version.json'
    $trackedVersion = @(Invoke-Git -GitArgs @('ls-tree', '--name-only', 'HEAD', '--', 'frontend/version.json'))
    $alreadyApplied = ($trackedVersion.Count -gt 0) -and
        ((Get-Content -Raw -LiteralPath $versionPath | ConvertFrom-Json).version -eq $Release)
    if (-not $alreadyApplied) {
        Invoke-Git -GitArgs @('apply', '--check', '--index', $PatchPath)
        $backup = 'backup/before-web-' + (Get-Date -Format 'yyyyMMdd-HHmmss')
        Invoke-Git -GitArgs @('branch', $backup)
        Invoke-Git -GitArgs @('apply', '--index', $PatchPath)
        Write-Host "Prepared update. Local backup: $backup"
        Invoke-Git -GitArgs @('commit', '-m', $CommitMessage)
    }
    Invoke-Git -GitArgs @('push', 'origin', 'main')
    Write-Host "Website $Release pushed to GitHub main."
    Write-Host 'Resume the existing service at https://dashboard.render.com and deploy latest main.'
    Write-Host 'Deploy main on Netlify too. Verify /version.json after deployment.'
    Write-Host 'Fleng opens in a normal browser. No app or EXE is installed.'
} catch {
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host 'Stopped. No forced push or data deletion was performed.'
    Write-Host 'If a commit was created but push failed, run this updater again after fixing Git access.'
    Write-Host 'If commit failed, the prepared changes remain staged; review git status before continuing.'
    exit 1
}
