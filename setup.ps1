<#
.SYNOPSIS
    NeuralStark - Windows Setup Script
.DESCRIPTION
    Installs all dependencies and sets up the NeuralStark on Windows
.NOTES
    Requires PowerShell 5.1 or higher
#>

# Require PowerShell 5.1 or higher
#Requires -Version 5.1

# Set error action preference
$ErrorActionPreference = "Stop"

# Colors for output
function Write-Step {
    param($Message)
    Write-Host "`n===================================================" -ForegroundColor Blue
    Write-Host "  $Message" -ForegroundColor Blue
    Write-Host "===================================================" -ForegroundColor Blue
}

function Write-Success {
    param($Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
}

function Write-Error-Custom {
    param($Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

function Write-Warning-Custom {
    param($Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Test-CommandExists {
    param($Command)
    try {
        if (Get-Command $Command -ErrorAction Stop) {
            return $true
        }
    }
    catch {
        return $false
    }
    return $false
}

# Main setup function
function Start-RagSetup {
    Write-Host @"
╔══════════════════════════════════════════════════════════════╗
║                 NeuralStark Setup for Windows              ║
║                                                              ║
║  This script will install and configure:                    ║
║  - Python 3.11+                                             ║
║  - Node.js 18+                                              ║
║  - MongoDB 7.0+                                             ║
║  - pm2 Process Manager                                      ║
║  - All Python and Node.js dependencies                      ║
╚══════════════════════════════════════════════════════════════╝
"@ -ForegroundColor Cyan

    # Check if running as administrator
    if (-not (Test-Administrator)) {
        Write-Warning-Custom "Some installations require administrator privileges."
        Write-Warning-Custom "Consider running this script as Administrator for best results."
        $continue = Read-Host "Continue anyway? (y/N)"
        if ($continue -ne 'y') {
            exit 1
        }
    }

    # Step 1: Check Python
    Write-Step "Step 1/8: Checking Python Installation"
    if (Test-CommandExists python) {
        $pythonVersion = python --version
        Write-Success "Python is installed: $pythonVersion"
    }
    else {
        Write-Error-Custom "Python is not installed!"
        Write-Host "Please install Python 3.11+ from: https://www.python.org/downloads/" -ForegroundColor Yellow
        Write-Host "Make sure to check 'Add Python to PATH' during installation" -ForegroundColor Yellow
        exit 1
    }

    # Step 2: Check Node.js
    Write-Step "Step 2/8: Checking Node.js Installation"
    if (Test-CommandExists node) {
        $nodeVersion = node --version
        Write-Success "Node.js is installed: $nodeVersion"
    }
    else {
        Write-Error-Custom "Node.js is not installed!"
        Write-Host "Please install Node.js 18+ from: https://nodejs.org/" -ForegroundColor Yellow
        exit 1
    }

    # Step 3: Check MongoDB
    Write-Step "Step 3/8: Checking MongoDB Installation"
    if (Test-CommandExists mongod) {
        Write-Success "MongoDB is installed"
    }
    else {
        Write-Warning-Custom "MongoDB is not detected!"
        Write-Host "Install options:" -ForegroundColor Yellow
        Write-Host "  1. Download installer: https://www.mongodb.com/try/download/community" -ForegroundColor Yellow
        Write-Host "  2. Or use Chocolatey: choco install mongodb" -ForegroundColor Yellow
        $continue = Read-Host "Continue without MongoDB? (services won't start) (y/N)"
        if ($continue -ne 'y') {
            exit 1
        }
    }

    # Step 4: Create Python Virtual Environment
    Write-Step "Step 4/8: Creating Python Virtual Environment"
    if (Test-Path ".venv") {
        Write-Success "Virtual environment already exists"
    }
    else {
        Write-Host "Creating virtual environment..."
        python -m venv .venv
        Write-Success "Virtual environment created"
    }

    # Step 5: Install Python Dependencies
    Write-Step "Step 5/8: Installing Python Dependencies"
    Write-Host "Activating virtual environment..."
    & .\.venv\Scripts\Activate.ps1
    
    Write-Host "Upgrading pip..."
    python -m pip install --upgrade pip setuptools wheel
    
    Write-Host "Installing backend dependencies..."
    Set-Location backend
    pip install -r requirements.txt
    Set-Location ..
    Write-Success "Python dependencies installed"

    # Step 6: Install Node.js Dependencies
    Write-Step "Step 6/8: Installing Node.js Dependencies"
    if (Test-CommandExists yarn) {
        Write-Success "Yarn is installed"
    }
    else {
        Write-Host "Installing Yarn globally..."
        npm install -g yarn
    }
    
    Write-Host "Installing frontend dependencies..."
    Set-Location frontend
    yarn install
    Set-Location ..
    Write-Success "Node.js dependencies installed"

    # Step 7: Install pm2
    Write-Step "Step 7/8: Installing pm2 Process Manager"
    if (Test-CommandExists pm2) {
        Write-Success "pm2 is already installed"
    }
    else {
        Write-Host "Installing pm2 globally..."
        npm install -g pm2
        Write-Success "pm2 installed"
    }

    # Step 8: Create Environment Files
    Write-Step "Step 8/8: Creating Environment Files"
    
    # Backend .env
    if (-not (Test-Path "backend\.env")) {
        Write-Host "Creating backend .env file..."
        @"
# NeuralStark Backend Environment
# Generated: $(Get-Date)

# MongoDB Configuration
MONGO_URL=mongodb://localhost:27017
DB_NAME=rag_platform

# CORS Configuration
CORS_ORIGINS=*

# Note: Cache paths are set automatically in config_paths.py
# This ensures cross-platform compatibility (Windows/Linux/macOS)
"@ | Out-File -FilePath "backend\.env" -Encoding UTF8
        Write-Success "Backend .env created"
    }
    else {
        Write-Success "Backend .env already exists"
    }
    
    # Frontend .env
    if (-not (Test-Path "frontend\.env")) {
        Write-Host "Creating frontend .env file..."
        @"
# NeuralStark Frontend Environment
# Generated: $(Get-Date)

# Backend API URL
REACT_APP_BACKEND_URL=http://localhost:8001

# WebSocket configuration
WDS_SOCKET_PORT=0
"@ | Out-File -FilePath "frontend\.env" -Encoding UTF8
        Write-Success "Frontend .env created"
    }
    else {
        Write-Success "Frontend .env already exists"
    }

    # Create logs directory
    if (-not (Test-Path "logs")) {
        New-Item -ItemType Directory -Path "logs" | Out-Null
        Write-Success "Logs directory created"
    }

    # Setup complete
    Write-Host "`n" -NoNewline
    Write-Host @"
╔══════════════════════════════════════════════════════════════╗
║              Setup Complete! 🎉                              ║
╚══════════════════════════════════════════════════════════════╝

Next steps:
1. Start MongoDB service (if not running):
   net start MongoDB

2. Start NeuralStark:
   .\start.ps1

3. Access the application:
   Frontend: http://localhost:3000
   Backend:  http://localhost:8001

Useful commands:
- View status: pm2 status
- View logs:   pm2 logs
- Stop all:    .\stop.ps1
- Restart:     pm2 restart all

"@ -ForegroundColor Green
}

# Run setup
try {
    Start-RagSetup
}
catch {
    Write-Error-Custom "Setup failed: $_"
    exit 1
}
