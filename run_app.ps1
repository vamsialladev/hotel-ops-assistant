# One-click local run on Windows:  right-click > "Run with PowerShell", or:  .\run_app.ps1
# Uses the .venv in this folder, checks .env, builds the search index if it's missing, then starts the
# app on http://localhost:8501. Stop it with Ctrl+C.

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

function Stop-WithMessage($message) {
    Write-Host ""
    Write-Host $message -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to close"
    exit 1
}

$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    Stop-WithMessage @"
No virtual environment found in .venv. Create it once with:
    py -3.12 -m venv .venv
    .\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
"@
}

if (-not (Test-Path (Join-Path $PSScriptRoot ".env"))) {
    Stop-WithMessage @"
No .env file found. Create it from the template and add your Anthropic API key:
    copy .env.example .env
    notepad .env
"@
}

if (-not (Test-Path (Join-Path $PSScriptRoot "data\index\chunks.json"))) {
    Write-Host "Building the search index (first run only)..." -ForegroundColor Cyan
    & $python -m src.ingest
    if ($LASTEXITCODE -ne 0) { Stop-WithMessage "Building the index failed. See the messages above." }
}

Write-Host "Starting the app at http://localhost:8501 (Ctrl+C to stop)..." -ForegroundColor Green
& $python -m streamlit run app.py --server.port 8501
