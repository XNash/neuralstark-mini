<#
.SYNOPSIS
    Start RAG Platform services on Windows
#>

$ErrorActionPreference = "Stop"

Write-Host "Starting RAG Platform..." -ForegroundColor Cyan

# Check if MongoDB is running
$mongoService = Get-Service -Name MongoDB -ErrorAction SilentlyContinue
if ($mongoService -and $mongoService.Status -eq 'Running') {
    Write-Host "[OK] MongoDB is running" -ForegroundColor Green
}
else {
    Write-Host "[WARNING] MongoDB service is not running!" -ForegroundColor Yellow
    Write-Host "Start MongoDB with: net start MongoDB" -ForegroundColor Yellow
}

# Check if pm2 is installed
if (-not (Get-Command pm2 -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] pm2 is not installed!" -ForegroundColor Red
    Write-Host "Install with: npm install -g pm2" -ForegroundColor Yellow
    exit 1
}

# Create logs directory if it doesn't exist
if (-not (Test-Path "logs")) {
    New-Item -ItemType Directory -Path "logs" | Out-Null
}

# Start services with pm2
Write-Host "Starting services with pm2..." -ForegroundColor Cyan
pm2 start ecosystem.config.js

# Save pm2 configuration
pm2 save

Write-Host "`n" -NoNewline
Write-Host @"
╔══════════════════════════════════════════════════════════════╗
║              RAG Platform Started! 🚀                        ║
╚══════════════════════════════════════════════════════════════╝

Services:
- Backend:  http://localhost:8001
- Frontend: http://localhost:3000

Useful commands:
- View status: pm2 status
- View logs:   pm2 logs
- Stop all:    .\stop.ps1
- Restart:     pm2 restart all

"@ -ForegroundColor Green