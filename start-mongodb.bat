@echo off
echo ========================================
echo MongoDB Database
echo ========================================
echo.
echo Starting MongoDB...
echo.

REM Check if MongoDB is installed as a service
sc query MongoDB >nul 2>&1
if %errorlevel% equ 0 (
    echo Starting MongoDB service...
    net start MongoDB
    if errorlevel 1 (
        echo MongoDB service failed to start
        echo Trying manual start...
    ) else (
        echo MongoDB service started successfully!
        echo Connection: mongodb://localhost:27017
        pause
        exit /b 0
    )
)

REM Manual start if service not available
echo MongoDB service not found, starting manually...
echo.

REM Create data directory if it doesn't exist
if not exist "C:\data\db" (
    echo Creating data directory: C:\data\db
    mkdir C:\data\db
)

echo Data directory: C:\data\db
echo Connection: mongodb://localhost:27017
echo.
echo Press Ctrl+C to stop MongoDB
echo ========================================
echo.

mongod --dbpath C:\data\db

if errorlevel 1 (
    echo.
    echo ERROR: Failed to start MongoDB!
    echo.
    echo Possible solutions:
    echo 1. Install MongoDB from: https://www.mongodb.com/try/download/community
    echo 2. Create directory: mkdir C:\data\db
    echo 3. Check if MongoDB is already running
    echo 4. Check if port 27017 is available
    pause
)
