@echo off
echo ========================================
echo Stopping NeuralStark Services
echo ========================================
echo.

echo Stopping frontend (port 3000)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3000') do (
    taskkill /PID %%a /F >nul 2>&1
)

echo Stopping backend (port 8001)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8001') do (
    taskkill /PID %%a /F >nul 2>&1
)

echo.
echo Services stopped!
echo.

echo Do you want to stop MongoDB as well? (Y/N)
set /p stop_mongo=

if /i "%stop_mongo%"=="Y" (
    echo Stopping MongoDB service...
    net stop MongoDB >nul 2>&1
    if errorlevel 1 (
        echo MongoDB service not found or already stopped
        echo Checking for MongoDB process...
        for /f "tokens=2" %%a in ('tasklist ^| findstr mongod') do (
            taskkill /PID %%a /F >nul 2>&1
        )
    ) else (
        echo MongoDB service stopped
    )
)

echo.
echo All services stopped!
echo.
pause
