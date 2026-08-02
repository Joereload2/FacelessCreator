$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

python -m PyInstaller --noconfirm --clean FacelessCreator.spec
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller failed with exit code $LASTEXITCODE"
}

$executable = Join-Path $projectRoot 'dist\FacelessCreator.exe'
if (-not (Test-Path -LiteralPath $executable -PathType Leaf)) {
    throw "Executable was not created: $executable"
}

Write-Host "Built $executable"
