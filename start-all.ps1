# One-click start: backend + frontend (+ ngrok if installed). Run from the project root:  .\start-all.ps1
$root = $PSScriptRoot
$backend = Join-Path $root "backend"
$frontend = Join-Path $root "frontend"

if (-not (Test-Path "$backend\.venv")) {
  Write-Host "Setting up backend (first run)..."
  Push-Location $backend
  python -m venv .venv
  & .\.venv\Scripts\python.exe -m pip install -r requirements.txt
  if (-not (Test-Path .env)) { Copy-Item .env.example .env }
  Pop-Location
}
if (-not (Test-Path "$frontend\node_modules")) {
  Write-Host "Installing frontend packages (first run)..."
  Push-Location $frontend; npm install; Pop-Location
}
if (-not (Test-Path "$frontend\.env")) { Copy-Item "$frontend\.env.example" "$frontend\.env" }

Start-Process powershell -ArgumentList "-NoExit","-Command","cd '$backend'; .\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000"
Start-Sleep -Seconds 4
Start-Process powershell -ArgumentList "-NoExit","-Command","cd '$frontend'; npm run dev"
Start-Sleep -Seconds 4

if (Get-Command ngrok -ErrorAction SilentlyContinue) {
  Start-Process powershell -ArgumentList "-NoExit","-Command","ngrok http 5173"
  Write-Host "ngrok started. Copy the https://...ngrok-free.app link from the ngrok window."
} else {
  Write-Host "ngrok not installed: skipping public link. Install with: winget install ngrok.ngrok"
}
Write-Host "Open http://localhost:5173  (demo login: demo@agri360.example / Demo@12345)"
