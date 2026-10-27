param(
    [string]$Results,
    [ValidateRange(1, 60)][int]$RefreshSeconds = 5,
    [switch]$Once
)

$ErrorActionPreference = 'Stop'
if (-not $Results) {
    $Results = Join-Path (Split-Path $PSScriptRoot -Parent) 'experiments/results/partial-feedback-pilot-d076-2026-10-27'
}
$taskRoot = [IO.Path]::GetFullPath($Results)

function Show-PilotCheckpoint {
    $progressPath = Join-Path $taskRoot 'progress.json'
    $stopPath = Join-Path $taskRoot 'STOP.json'
    $progressFile = Get-Item -LiteralPath $progressPath -ErrorAction SilentlyContinue
    $stopFile = Get-Item -LiteralPath $stopPath -ErrorAction SilentlyContinue
    if ($stopFile -and (-not $progressFile -or $stopFile.LastWriteTimeUtc -ge $progressFile.LastWriteTimeUtc)) {
        $stopped = Get-Content -LiteralPath $stopPath -Raw | ConvertFrom-Json
        Write-Output "STOPPED at snapshot $($stopped.index): $($stopped.error)"
        Write-Output 'No outcome evaluation is claimed. Read STOP.json before resuming.'
        return
    }
    if (-not (Test-Path -LiteralPath $progressPath)) {
        Write-Output 'No checkpoint is available yet. This does not establish whether a study process is running.'
        return
    }
    $progress = Get-Content -LiteralPath $progressPath -Raw | ConvertFrom-Json
    $age = [Math]::Max(0, [int]((Get-Date).ToUniversalTime() - (Get-Item -LiteralPath $progressPath).LastWriteTimeUtc).TotalSeconds)
    if ($progress.phase -eq 'source_mapping') {
        $completed = [int]$progress.completed
        $total = [int]$progress.total
        if ($total -le 0 -or $completed -lt 0 -or $completed -gt $total) { throw 'Invalid mapping checkpoint counters.' }
        $filled = [int][Math]::Floor(30 * $completed / $total)
        $bar = ('#' * $filled) + ('-' * (30 - $filled))
        Write-Output "[$bar] $completed/$total source snapshots mapped"
        Write-Output 'This bar covers source mapping only. Policy replay and outcome evaluation follow it.'
    } elseif ($progress.phase -eq 'replay') {
        Write-Output 'Source mapping complete. Policy replay is in progress; no percentage is available.'
    } elseif ($progress.phase -eq 'complete' -and $progress.outcomes_evaluated -eq $true) {
        if (-not (Test-Path -LiteralPath (Join-Path $taskRoot 'results.json'))) { throw 'Completion checkpoint has no results.json.' }
        Write-Output 'COMPLETE: policy replay results are saved. This is a development pilot, not a deployment guarantee.'
    } else {
        Write-Output "Recorded phase: $($progress.phase)"
    }
    Write-Output "Last checkpoint: $age seconds ago. Checkpoint age alone does not prove that a process is stuck or running."
}

do {
    if (-not $Once) { Clear-Host }
    Write-Output 'CodeDNA partial-feedback development pilot'
    Write-Output "Results: $taskRoot"
    try { Show-PilotCheckpoint }
    catch {
        if ($Once) { throw }
        Write-Output "Could not read the checkpoint: $($_.Exception.Message)"
    }
    Write-Output 'Read only: this viewer never starts, restarts, cancels or changes a study.'
    if (-not $Once) {
        Write-Output "Refresh: $RefreshSeconds seconds. Ctrl+C closes this viewer only."
        Start-Sleep -Seconds $RefreshSeconds
    }
} while (-not $Once)
