@echo off
echo Stopping PetCare Development Servers...
echo.

REM Kill Django development server (usually runs on port 8000)
echo Stopping Django backend server...
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8000" ^| find "LISTENING"') do (
    echo Killing Django process with PID: %%a
    taskkill /PID %%a /F >nul 2>&1
)

REM Kill Svelte development server (usually runs on port 5173)
echo Stopping Svelte frontend server...
for /f "tokens=5" %%a in ('netstat -aon ^| find ":5173" ^| find "LISTENING"') do (
    echo Killing Svelte process with PID: %%a
    taskkill /PID %%a /F >nul 2>&1
)

REM Alternative method: Kill by process name
echo Stopping any remaining Node.js processes (Svelte)...
taskkill /IM node.exe /F >nul 2>&1

echo Stopping any remaining Python processes (Django)...
taskkill /IM python.exe /F >nul 2>&1

REM Close any terminal windows with specific titles
echo Closing development terminal windows...
taskkill /FI "WINDOWTITLE eq Django Backend*" >nul 2>&1
taskkill /FI "WINDOWTITLE eq Svelte Frontend*" >nul 2>&1
