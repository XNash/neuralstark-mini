@echo off
echo ========================================
echo NeuralStark - Windows Setup
echo ========================================
echo.
echo This script will help you set up NeuralStark
echo.

cd /d "%~dp0"

REM Check Python
echo [1/5] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found!
    echo Please install Python 3.10+ from: https://www.python.org/downloads/
    pause
    exit /b 1
)
python --version
echo.

REM Check Node.js
echo [2/5] Checking Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js not found!
    echo Please install Node.js 18+ from: https://nodejs.org/
    pause
    exit /b 1
)
node --version
npm --version
echo.

REM Setup Python virtual environment
echo [3/5] Setting up Python virtual environment...
cd backend

if exist "venv" (
    echo Virtual environment already exists
) else (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment!
        pause
        exit /b 1
    )
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Installing Python dependencies...
echo This may take several minutes...
pip install --upgrade pip
pip install -r requirements.txt

if errorlevel 1 (
    echo WARNING: Some packages may have failed to install
    echo The application may still work if core packages are installed
)

cd ..
echo.

REM Setup frontend
echo [4/5] Installing frontend dependencies...
cd frontend

if exist "node_modules" (
    echo node_modules already exists, skipping...
) else (
    echo Installing npm packages...
    echo This may take several minutes...
    npm install
    if errorlevel 1 (
        echo ERROR: Failed to install frontend dependencies!
        pause
        exit /b 1
    )
)

cd ..
echo.

REM Create directories
echo [5/5] Creating directories...
if not exist "files" mkdir files
if not exist ".cache\huggingface" mkdir ".cache\huggingface"
if not exist ".cache\sentence_transformers" mkdir ".cache\sentence_transformers"
echo.

REM Create sample documents if none exist
if not exist "files\company_info.md" (
    echo Creating sample documents...
    (
        echo # TechCorp - Company Information
        echo.
        echo ## About Us
        echo TechCorp is a leading technology company providing innovative solutions.
        echo.
        echo **Founded:** 2020
        echo **Location:** San Francisco, CA
        echo.
        echo ## Contact
        echo - Email: info@techcorp.com
        echo - Phone: +1-555-0123
    ) > "files\company_info.md"
    
    (
        echo TechCorp Products
        echo.
        echo 1. CloudSync Pro - $99/month
        echo 2. DataVault - $149/month
        echo 3. AI Assistant - $199/month
    ) > "files\products.txt"
echo.
)

echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Next steps:
echo.
echo 1. Start MongoDB:
 echo    start-mongodb.bat
echo.
echo 2. Start Backend (new terminal):
echo    start-backend.bat
echo.
echo 3. Start Frontend (new terminal):
echo    start-frontend.bat
echo.
echo 4. Open browser: http://localhost:3000
echo.
echo 5. Add your Gemini API key in Settings
echo    Get it from: https://aistudio.google.com/app/apikey
echo.
echo See MANUAL_SETUP_WINDOWS.md for detailed instructions
echo.
pause
