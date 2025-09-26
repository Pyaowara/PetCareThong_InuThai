@echo off
echo Restarting PetCare Development Environment...
echo.

echo Step 1: Stopping all development servers...
call stop.bat

echo.
echo Waiting 2 seconds before restart...
timeout /t 2 /nobreak >nul

echo.
echo Step 2: Starting development servers...
call start-dev.bat

echo.
echo Restart complete!