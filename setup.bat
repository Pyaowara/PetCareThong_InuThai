@echo off
echo Setting up PetCare Development Environment...
echo This script will set up both backend (Django) and frontend (Svelte) environments
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python first and add it to your PATH
    pause
    exit /b 1
)

echo Python found: 
python --version

REM Check if Node.js is installed
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Node.js is not installed or not in PATH
    echo Please install Node.js first and add it to your PATH
    echo You can download it from: https://nodejs.org/
    pause
    exit /b 1
)

echo Node.js found and working!
echo.

REM Check if pnpm is installed
echo Checking for pnpm installation...
where pnpm >nul 2>&1
echo test
if %errorlevel% neq 0 (
    echo pnpm not found, installing pnpm globally...
    npm install -g pnpm
    if %errorlevel% neq 0 (
        echo Error: Failed to install pnpm
        echo Please install pnpm manually: npm install -g pnpm
        pause
        exit /b 1
    )
    echo pnpm installed successfully!
)

echo pnpm found and working!
echo.

REM Create virtual environment if it doesn't exist
if not exist "myvenv" (
    echo Creating virtual environment...
    python -m venv myvenv
    if %errorlevel% neq 0 (
        echo Error: Failed to create virtual environment
        pause
        exit /b 1
    )
    echo Virtual environment created successfully!
) else (
    echo Virtual environment already exists, skipping creation...
)

echo.
echo Activating virtual environment...
call myvenv\Scripts\activate.bat

REM Upgrade pip first
echo.
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install Django
echo.
echo Installing Django...
pip install -r requirements.txt 

echo.
echo Backend Python packages installed successfully!
echo.
echo Installed Python packages:
pip list

echo.
echo ========================================
echo Setting up Frontend (Svelte)...
echo ========================================
echo.

REM Create Svelte project if it doesn't exist
if not exist "frontend" (
    echo Creating Svelte project...
    npx sv create frontend --template minimal --types typescript --no-add-ons --package-manager pnpm --no-install
    if %errorlevel% neq 0 (
        echo Error: Failed to create Svelte project
        pause
        exit /b 1
    )
    echo Svelte project created successfully!
) else (
    echo Svelte project already exists, skipping creation...
)

REM Install frontend dependencies
echo.
echo Installing frontend dependencies...
cd frontend
if exist "package.json" (
    echo Installing packages with pnpm...
    pnpm install
    if %errorlevel% neq 0 (
        echo Error: Failed to install frontend dependencies with pnpm
        echo Please check your pnpm installation or network connection
        cd ..
        pause
        exit /b 1
    )
    echo Frontend dependencies installed successfully with pnpm!
) else (
    echo Error: package.json not found in frontend directory
    cd ..
    pause
    exit /b 1
)

cd ..

echo.
echo ========================================
echo Setup completed successfully!
echo ========================================
echo.
echo Backend (Django):
echo - Virtual environment: myvenv
echo - Django, psycopg2-binary, django-cors-headers installed
echo.
echo Frontend (Svelte):
echo - Project created in: frontend/
echo - Dependencies installed
echo.
echo Next steps:
echo 1. Run start-dev.bat to start both servers
echo 2. Visit http://localhost:5173/ for frontend
echo 3. Visit http://127.0.0.1:8000/ for backend
echo.
echo Development commands:
echo - start-dev.bat : Start both servers
echo - stop.bat      : Stop both servers
echo.
echo To activate Python environment manually:
echo call myvenv\Scripts\activate.bat
echo.
echo To run frontend manually:
echo cd frontend && pnpm run dev
echo.

pause