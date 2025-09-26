@echo off
echo Activating PetCare Virtual Environment...
echo.

REM Check if virtual environment exists
if not exist "myvenv" (
    echo Error: Virtual environment not found!
    echo Please run setup.bat first to create the virtual environment.
    echo.
    pause
    exit /b 1
)

REM Activate virtual environment and change to Django directory
echo Activating virtual environment and navigating to Django directory...
echo.
echo 📁 Current location: %CD%\petcare
echo 🐍 Virtual environment: myvenv
echo.
echo You are now in the Django project directory with venv activated!
echo Available commands:
echo   - python manage.py runserver
echo   - python manage.py migrate  
echo   - python manage.py makemigrations
echo   - python manage.py shell
echo.

REM Change to petcare directory and activate venv in a new persistent session
cmd /k "cd petcare && ..\myvenv\Scripts\activate.bat"