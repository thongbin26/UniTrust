param(
    [string]$OcrPython = $env:UNITRUST_OCR_PYTHON
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($OcrPython)) {
    throw "Set UNITRUST_OCR_PYTHON to the isolated OCR runtime python.exe; main .venv is never used."
}
if (-not (Test-Path -LiteralPath $OcrPython -PathType Leaf)) {
    throw "Isolated OCR Python was not found: $OcrPython"
}

$repoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $repoRoot
try {
    & $OcrPython -m scripts.ocr_sidecar
} finally {
    Pop-Location
}
