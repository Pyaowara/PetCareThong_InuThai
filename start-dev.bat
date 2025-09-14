@echo off
echo Starting PetCare Development Environment...
echo.

REM Check if virtual environment exists
if not exist "myvenv" (
    echo Error: Virtual environment not found. Please run setup.bat first.
    pause
    exit /b 1
)

REM Check if frontend directory exists
if not exist "frontend" (
    echo Error: Frontend directory not found. Please create Svelte project first.
    pause
    exit /b 1
)

echo Starting Django backend server...
start "Django Backend" cmd /k "cd petcare && ..\myvenv\Scripts\activate.bat && python manage.py runserver"

echo Waiting 3 seconds for Django to start...
timeout /t 3 /nobreak >nul

echo Starting Svelte frontend server...
start "Svelte Frontend" cmd /k "cd frontend && pnpm run dev"

echo.
echo Development servers are starting...
echo.
echo Django Backend: http://127.0.0.1:8000/
echo Svelte Frontend: http://localhost:5173/
echo.
echo Press any key to close this window (servers will continue running)
pause