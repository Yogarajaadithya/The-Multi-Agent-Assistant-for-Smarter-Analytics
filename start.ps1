# Start Backend (FastAPI + Uvicorn)
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$PSScriptRoot\backend-repo'; uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

# Start Frontend (Vite)
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$PSScriptRoot\frontend-repo'; npm run dev"

Write-Host ""
Write-Host "Servers starting..."
Write-Host "  Backend  -> http://localhost:8000"
Write-Host "  Frontend -> http://localhost:5173"
Write-Host ""
