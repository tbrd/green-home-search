# Start both the FastAPI server and the Vite dev server for local development
# Usage: .\scripts\start-dev.ps1

$ErrorActionPreference = 'Stop'

$repo = Split-Path -Parent $MyInvocation.MyCommand.Definition
$apiDir = Join-Path $repo '../api'
$webDir = Join-Path $repo '../web'

Write-Host "Starting API (uvicorn)..."

# Start uvicorn in a new window
$uvicornCmd = "powershell -NoExit -Command `"cd '$apiDir'; if (Test-Path .venv) { .\.venv\Scripts\Activate.ps1 }; uvicorn main:app --reload --port 8000`""
Start-Process -FilePath powershell -ArgumentList "-NoExit","-Command","cd '$apiDir'; if (Test-Path .venv) { .\.venv\Scripts\Activate.ps1 }; uvicorn main:app --reload --port 8000"

Write-Host "Ready."
