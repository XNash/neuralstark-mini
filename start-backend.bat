@echo off
echo ========================================
echo NeuralStark Backend
echo ========================================
echo.
echo Starting backend server on port 8001...
echo.

cd /d "%~dp0backend"

if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found!
    echo Please run: python -m venv venv
    echo Then: venv\Scripts\activate
    echo Then: pip install -r requirements.txt
    pause
    exit /b 1
)

call venv\Scripts\activate.bat

echo Virtual environment activated
echo Python: %VIRTUAL_ENV%
echo.
echo Backend will run on: http://localhost:8001
echo API documentation: http://localhost:8001/docs
echo.
echo Press Ctrl+C to stop the server
echo ========================================
echo.

uvicorn server:app --host 0.0.0.0 --port 8001 --reload

if errorlevel 1 (
    echo.
    echo ERROR: Failed to start backend!
    echo Check if:
    echo - MongoDB is running
    echo - Port 8001 is available
    echo - All dependencies are installed
    pause
)
