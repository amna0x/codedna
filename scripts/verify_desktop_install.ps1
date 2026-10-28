param(
    [Parameter(Mandatory = $true)][string]$AppDirectory,
    [string]$Report = "codedna-clean-pc-smoke.json"
)
$ErrorActionPreference = "Stop"
$resolvedApp = (Resolve-Path -LiteralPath $AppDirectory).Path
$coreDirectory = Join-Path $resolvedApp "resources/core"
$core = Join-Path $coreDirectory "codedna-core.exe"
$manifestPath = Join-Path $coreDirectory "bundle-manifest.json"
if (!(Test-Path -LiteralPath $core) -or !(Test-Path -LiteralPath $manifestPath)) {
    throw "Choose the installed CodeDNA app directory containing resources/core."
}
$manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
$verified = 0
foreach ($entry in $manifest.files.PSObject.Properties) {
    $file = [IO.Path]::GetFullPath((Join-Path $coreDirectory $entry.Name))
    $prefix = [IO.Path]::GetFullPath($coreDirectory).TrimEnd('\') + '\'
    if (!$file.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) { throw "Invalid manifest path." }
    if ((Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash.ToLowerInvariant() -ne $entry.Value) {
        throw "Bundle hash mismatch: $($entry.Name)"
    }
    $verified++
}
$version = & $core --version
if ($LASTEXITCODE -ne 0) { throw "Bundled core did not start." }
$pluginJson = & $core plugins
if ($LASTEXITCODE -ne 0) { throw "Bundled plugin discovery failed." }
$plugins = $pluginJson | ConvertFrom-Json
foreach ($language in @('java', 'python')) {
    if ($language -notin $plugins.plugins.name) { throw "Bundled language missing: $language" }
}
$result = [ordered]@{
    checked_at_utc = [DateTime]::UtcNow.ToString('o')
    scope = "Installed payload smoke; GUI/build acceptance and clean-machine provenance require human confirmation."
    status = "automated_smoke_passed_manual_pending"
    os = [Environment]::OSVersion.VersionString
    core_version = ($version -join "`n").Trim()
    verified_files = $verified
    plugins = @($plugins.plugins.name)
    git_available = [bool](Get-Command git -ErrorAction SilentlyContinue)
    external_python_on_path = [bool](Get-Command python -ErrorAction SilentlyContinue)
    manual_checks = @('Fresh Windows provenance', 'IDE launch', 'Extensions/Language plugins',
        'Open project and analyse change', 'Test execution with prerequisites', 'Uninstall')
}
$result | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $Report -Encoding utf8
Write-Output "Installed payload verified ($verified files). Complete the manual checks; report: $Report"
