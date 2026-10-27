param([Parameter(Mandatory)][string]$Viewer)
$ErrorActionPreference = 'Stop'
$taskRoot = Join-Path ([IO.Path]::GetTempPath()) ('codedna-viewer-test-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $taskRoot | Out-Null
& git -C $taskRoot init --quiet
if ($LASTEXITCODE -ne 0) { throw 'Could not create temporary Git fixture.' }
$progress = Join-Path $taskRoot 'progress.json'
$stop = Join-Path $taskRoot 'STOP.json'
$results = Join-Path $taskRoot 'results.json'
$passed = 0
function Assert-Text([string]$Output, [string]$Pattern) {
    if ($Output -notmatch $Pattern) { throw "Expected '$Pattern' in '$Output'" }
}
$output = (& $Viewer -Results $taskRoot -Once) -join "`n"
Assert-Text $output 'No checkpoint'; Assert-Text $output 'does not establish'; $passed++
'{"phase":"source_mapping","completed":60,"total":360,"outcomes_evaluated":false}' | Set-Content -LiteralPath $progress
$before = (Get-FileHash -LiteralPath $progress).Hash
$output = (& $Viewer -Results $taskRoot -Once) -join "`n"
Assert-Text $output '60/360'; Assert-Text $output 'mapping only'
try {
    if ((Get-FileHash -LiteralPath $progress).Hash -ne $before) { throw 'Viewer modified progress.' }
    $passed++
    '{"phase":"replay","outcomes_evaluated":false}' | Set-Content -LiteralPath $progress
    $output = (& $Viewer -Results $taskRoot -Once) -join "`n"
    Assert-Text $output 'no percentage'; $passed++
    '{"phase":"complete","outcomes_evaluated":true}' | Set-Content -LiteralPath $progress
    $refused = $false
    try { & $Viewer -Results $taskRoot -Once | Out-Null } catch { $refused = $_.Exception.Message -match 'no results.json' }
    if (-not $refused) { throw 'Viewer accepted completion without results.' }; $passed++
    '{}' | Set-Content -LiteralPath $results
    $output = (& $Viewer -Results $taskRoot -Once) -join "`n"
    Assert-Text $output 'COMPLETE:'; Assert-Text $output 'not a deployment guarantee'; $passed++
    '{"index":7,"error":"mapping mismatch"}' | Set-Content -LiteralPath $stop
    $output = (& $Viewer -Results $taskRoot -Once) -join "`n"
    Assert-Text $output 'STOPPED'; Assert-Text $output 'mapping mismatch'; $passed++
    Write-Output "$passed viewer checks passed. Temporary Git fixture: $taskRoot"
} finally {
    # Keep the small fixture for inspection; no recursive deletion or study mutation.
}
