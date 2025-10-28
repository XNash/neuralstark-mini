# NeuralStark Windows PowerShell Startup Script
# Run this with: .\start-windows.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " NeuralStark - Windows Startup Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check Python
Write-Host "Checking prerequisites..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "[OK] Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python from https://www.python.org/downloads/" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Check Node.js
try {
    $nodeVersion = node --version 2>&1
    Write-Host "[OK] Node.js found: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Node.js is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Node.js from https://nodejs.org/" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Check Yarn
try {
    $yarnVersion = yarn --version 2>&1
    Write-Host "[OK] Yarn found: $yarnVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Yarn is not installed" -ForegroundColor Red
    Write-Host "Installing Yarn globally..." -ForegroundColor Yellow
    npm install -g yarn
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Failed to install Yarn" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
    Write-Host "[OK] Yarn installed" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Installing Dependencies" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Backend dependencies
Write-Host "Installing backend dependencies..." -ForegroundColor Yellow
Set-Location backend

if (-not (Test-Path "venv")) {
    Write-Host "Creating Python virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

& .\venv\Scripts\Activate.ps1
pip install -r requirements.txt -q
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Failed to install backend dependencies" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host "[OK] Backend dependencies installed" -ForegroundColor Green
deactivate

# Frontend dependencies
Write-Host "Installing frontend dependencies..." -ForegroundColor Yellow
Set-Location ..\frontend
yarn install --silent
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Failed to install frontend dependencies" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host "[OK] Frontend dependencies installed" -ForegroundColor Green

Set-Location ..

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Configuration Check" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check backend .env
if (-not (Test-Path "backend\.env")) {
    Write-Host "[WARNING] backend\.env not found" -ForegroundColor Yellow
    if (Test-Path "backend\.env.example") {
        Write-Host "Creating backend\.env from .env.example..." -ForegroundColor Yellow
        Copy-Item "backend\.env.example" "backend\.env"
        Write-Host "[ACTION REQUIRED] Please edit backend\.env and add your CEREBRAS_API_KEY" -ForegroundColor Red
    }
}

# Check frontend .env
if (-not (Test-Path "frontend\.env")) {
    Write-Host "[WARNING] frontend\.env not found" -ForegroundColor Yellow
    if (Test-Path "frontend\.env.example") {
        Write-Host "Creating frontend\.env from .env.example..." -ForegroundColor Yellow
        Copy-Item "frontend\.env.example" "frontend\.env"
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Starting Services" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Backend will start at: http://localhost:8001" -ForegroundColor Green
Write-Host "Frontend will start at: http://localhost:3000" -ForegroundColor Green
Write-Host ""
Write-Host "Press Ctrl+C to stop the services" -ForegroundColor Yellow
Write-Host ""

# Start backend in new window
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD\backend'; .\venv\Scripts\Activate.ps1; python server.py"

# Wait for backend to start
Write-Host "Waiting for backend to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

# Start frontend in current window
Set-Location frontend
Write-Host "Starting frontend..." -ForegroundColor Yellow
yarn start:win

# This line is reached when frontend is closed
Write-Host ""
Write-Host "Frontend stopped. Backend is still running in separate window." -ForegroundColor Yellow
Read-Host "Press Enter to exit"
