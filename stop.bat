@echo off
echo Stopping ProjectIQ services...
echo.

set STOPPED=0

echo [1/2] Stopping Backend (port 8000)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000" ^| findstr "LISTENING"') do (
    taskkill /F /PID %%a >nul 2>&1
    if not errorlevel 1 (
        echo   Stopped process PID %%a
        set STOPPED=1
    )
)

echo [2/2] Stopping Frontend (port 5173)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5173" ^| findstr "LISTENING"') do (
    taskkill /F /PID %%a >nul 2>&1
    if not errorlevel 1 (
        echo   Stopped process PID %%a
        set STOPPED=1
    )
)

echo.
if "%STOPPED%"=="1" (
    echo Services stopped successfully.
) else (
    echo No running services found on ports 8000 or 5173.
)
echo.
pause
