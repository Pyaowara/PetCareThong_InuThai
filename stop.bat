@echo off
echo Stopping PetCare Development Servers...
echo.

REM Kill processes by port first (more reliable)
echo Stopping Django backend server (port 8000)...
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8000" ^| find "LISTENING"') do (
    echo Killing process with PID: %%a
    taskkill /PID %%a /F >nul 2>&1
)

echo Stopping Svelte frontend server (port 5173)...
for /f "tokens=5" %%a in ('netstat -aon ^| find ":5173" ^| find "LISTENING"') do (
    echo Killing process with PID: %%a
    taskkill /PID %%a /F >nul 2>&1
)

REM Force close terminal windows by title (more aggressive)
echo Closing Django Backend terminal...
wmic process where "CommandLine like '%%Django Backend%%'" delete >nul 2>&1

echo Closing Svelte Frontend terminal...
wmic process where "CommandLine like '%%Svelte Frontend%%'" delete >nul 2>&1

REM Kill remaining processes by name
echo Cleaning up remaining processes...
taskkill /IM node.exe /F >nul 2>&1
taskkill /IM python.exe /F >nul 2>&1

REM Close CMD windows with specific titles using PowerShell (more reliable)
echo Closing development terminal windows...
powershell -Command "Get-Process | Where-Object {$_.MainWindowTitle -like '*Django Backend*' -or $_.MainWindowTitle -like '*Svelte Frontend*'} | Stop-Process -Force" >nul 2>&1

echo.
echo All development servers stopped!
echo Terminal windows closed!
echo.
pause
