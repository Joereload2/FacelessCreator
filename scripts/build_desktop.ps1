$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

python -m PyInstaller --noconfirm --clean FacelessCreatorSidecar.spec
if ($LASTEXITCODE -ne 0) {
    throw "Backend packaging failed with exit code $LASTEXITCODE"
}

$backend = Join-Path $projectRoot 'dist\FacelessCreatorBackend'
$binaryRoot = Join-Path $projectRoot 'src-tauri\binaries'
$sidecarDirectory = Join-Path $binaryRoot 'FacelessCreatorBackend'
$expectedSidecar = Join-Path $sidecarDirectory 'FacelessCreatorBackend.exe'
if (-not (Test-Path -LiteralPath $backend -PathType Container)) {
    throw "Backend directory was not created: $backend"
}
if (Test-Path -LiteralPath $sidecarDirectory) {
    $resolvedBinaryRoot = [IO.Path]::GetFullPath($binaryRoot)
    $resolvedSidecar = [IO.Path]::GetFullPath($sidecarDirectory)
    if ($resolvedSidecar -ne (Join-Path $resolvedBinaryRoot 'FacelessCreatorBackend')) {
        throw "Unexpected sidecar cleanup target: $resolvedSidecar"
    }
    Remove-Item -LiteralPath $resolvedSidecar -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $binaryRoot | Out-Null
Copy-Item -LiteralPath $backend -Destination $sidecarDirectory -Recurse
if (-not (Test-Path -LiteralPath $expectedSidecar -PathType Leaf)) {
    throw "Sidecar executable was not staged: $expectedSidecar"
}

npm.cmd exec tauri -- build --config src-tauri\tauri.conf.json
if ($LASTEXITCODE -ne 0) {
    throw "Tauri build failed with exit code $LASTEXITCODE"
}

Write-Host 'Desktop bundle built successfully.'
