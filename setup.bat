@echo off
echo 🏀 Basketball Simulation - Quick Start Script
echo ==============================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed. Please install Python 3.8 or higher.
    exit /b 1
)

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js is not installed. Please install Node.js 16 or higher.
    exit /b 1
)

echo ✓ Python and Node.js detected
echo.

REM Backend setup
echo 📦 Setting up backend...
cd backend

if not exist "venv" (
    echo Creating Python virtual environment...
    python -m venv venv
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Installing Python dependencies...
pip install -q -r requirements.txt

echo Initializing database and seeding data...
python seed_data.py

echo ✓ Backend setup complete!
echo.

REM Frontend setup
echo 📦 Setting up frontend...
cd ..\frontend

if not exist "node_modules" (
    echo Installing Node.js dependencies...
    npm install
)

echo ✓ Frontend setup complete!
echo.

echo ==============================================
echo ✅ Setup Complete!
echo.
echo To start the application:
echo.
echo Terminal 1 (Backend):
echo   cd backend
echo   venv\Scripts\activate.bat
echo   python app.py
echo.
echo Terminal 2 (Frontend):
echo   cd frontend
echo   npm start
echo.
echo Then open http://localhost:3000 in your browser
echo ==============================================
pause
