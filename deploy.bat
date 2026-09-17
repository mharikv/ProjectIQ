@echo off
setlocal enabledelayedexpansion

echo ========================================
echo  ProjectIQ - Production Deploy (Docker)
echo ========================================
echo.

where docker >nul 2>&1
if errorlevel 1 (
    echo Docker is not installed.
    echo Install Docker Desktop from: https://www.docker.com/products/docker-desktop/
    pause
    exit /b 1
)

if "%SECRET_KEY%"=="" (
    for /f "delims=" %%i in ('powershell -NoProfile -Command "[guid]::NewGuid().ToString('N')"') do set SECRET_KEY=%%i
    echo Generated SECRET_KEY for this session.
)

echo Building and starting ProjectIQ...
docker compose up --build -d

if errorlevel 1 (
    echo.
    echo Deploy failed. Check Docker Desktop is running.
    pause
    exit /b 1
)

echo.
echo ========================================
echo  ProjectIQ is live locally!
echo ========================================
echo  App:      http://localhost:8000
echo  API Docs: http://localhost:8000/docs
echo  Health:   http://localhost:8000/api/health
echo.
echo  Login: admin / admin123  or  pm_user / pm123
echo.
echo  To expose on the internet, run: start-tunnel.bat
echo  To stop: docker compose down
echo ========================================
echo.
pause
