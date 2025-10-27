@echo off
echo ========================================
echo NeuralStark Frontend
echo ========================================
echo.
echo Starting React development server...
echo.

cd /d "%~dp0frontend"

if not exist "node_modules" (
    echo ERROR: node_modules not found!
    echo Please run: npm install
    echo Or: yarn install
    pause
    exit /b 1
)

echo Dependencies found
echo.
echo Frontend will run on: http://localhost:3000
echo.
echo Press Ctrl+C to stop the server
echo ========================================
echo.

npm start

if errorlevel 1 (
    echo.
    echo ERROR: Failed to start frontend!
    echo Check if:
    echo - Node.js is installed
    echo - Port 3000 is available
    echo - Dependencies are installed (npm install)
    pause
)
