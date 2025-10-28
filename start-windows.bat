@echo off
REM Windows Batch Script to Start NeuralStark
REM This script checks prerequisites and starts both backend and frontend

echo ========================================
echo  NeuralStark - Windows Startup Script
echo ========================================
echo.

REM Check Python
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python from https://www.python.org/downloads/
    pause
    exit /b 1
)
echo [OK] Python found

REM Check Node.js
node --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Node.js is not installed or not in PATH
    echo Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)
echo [OK] Node.js found

REM Check Yarn
yarn --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Yarn is not installed
    echo Installing Yarn globally...
    npm install -g yarn
    if %ERRORLEVEL% NEQ 0 (
        echo Failed to install Yarn
        pause
        exit /b 1
    )
)
echo [OK] Yarn found

echo.
echo ========================================
echo  Installing Dependencies
echo ========================================
echo.

REM Install backend dependencies
echo Installing backend dependencies...
cd backend
if not exist venv (
    echo Creating Python virtual environment...
    python -m venv venv
)
call venv\Scripts\activate.bat
pip install -r requirements.txt -q
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to install backend dependencies
    pause
    exit /b 1
)
echo [OK] Backend dependencies installed
call venv\Scripts\deactivate.bat

REM Install frontend dependencies
echo Installing frontend dependencies...
cd ..\frontend
call yarn install --silent
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to install frontend dependencies
    pause
    exit /b 1
)
echo [OK] Frontend dependencies installed

cd ..

echo.
echo ========================================
echo  Configuration Check
echo ========================================
echo.

REM Check backend .env
if not exist backend\.env (
    echo [WARNING] backend\.env not found
    if exist backend\.env.example (
        echo Creating backend\.env from .env.example...
        copy backend\.env.example backend\.env
        echo [ACTION REQUIRED] Please edit backend\.env and add your CEREBRAS_API_KEY
    )
)

REM Check frontend .env
if not exist frontend\.env (
    echo [WARNING] frontend\.env not found
    if exist frontend\.env.example (
        echo Creating frontend\.env from .env.example...
        copy frontend\.env.example frontend\.env
    )
)

echo.
echo ========================================
echo  Starting Services
echo ========================================
echo.
echo Starting backend on http://localhost:8001
echo Starting frontend on http://localhost:3000
echo.
echo Press Ctrl+C to stop both services
echo.

REM Start backend in new window
start "NeuralStark Backend" cmd /k "cd backend && venv\Scripts\activate.bat && python server.py"

REM Wait a bit for backend to start
timeout /t 3 /nobreak >nul

REM Start frontend in current window
cd frontend
echo Starting frontend...
call yarn start:win

REM This line is reached when frontend is closed
echo.
echo Frontend stopped. Backend is still running in separate window.
pause
