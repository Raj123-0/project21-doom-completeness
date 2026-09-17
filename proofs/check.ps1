# Core-only validation. Run from any directory; no package manager/build download.
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$lean = Join-Path $env:USERPROFILE '.elan\bin\lean.exe'
Push-Location $root
try {
    Write-Output '> lean --version'
    & $lean --version
    if ($LASTEXITCODE -ne 0) { throw 'Lean version check failed' }
    $files = @(Get-ChildItem proofs,substrate,docs,paper -Recurse -Filter '*.lean' |
        Sort-Object FullName)
    if ($files.Count -ne 2) { throw "Expected two Lean artifacts; found $($files.Count)" }
    foreach ($file in $files) {
        $relative = $file.FullName.Substring($root.Length + 1)
        Write-Output "> lean -DwarningAsError=true $relative"
        & $lean -DwarningAsError=true $relative
        $code = $LASTEXITCODE
        Write-Output "Exit code: $code"
        if ($code -ne 0) { throw "Lean check failed: $relative" }
    }
    Write-Output "PASS: all $($files.Count) Lean files in allowed artifact directories checked."
} finally {
    Pop-Location
}
