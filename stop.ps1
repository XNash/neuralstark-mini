<#
.SYNOPSIS
    Stop RAG Platform services on Windows
#>

Write-Host "Stopping RAG Platform..." -ForegroundColor Cyan

if (Get-Command pm2 -ErrorAction SilentlyContinue) {
    pm2 stop ecosystem.config.js
    pm2 save
    Write-Host "[OK] Services stopped" -ForegroundColor Green
}
else {
    Write-Host "[ERROR] pm2 is not installed!" -ForegroundColor Red
    exit 1
}