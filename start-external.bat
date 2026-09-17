@echo off
echo Starting ProjectIQ (External Access)...
echo.

for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
    set LOCAL_IP=%%a
    goto :found_ip
)
:found_ip
set LOCAL_IP=%LOCAL_IP: =%

echo [1/2] Starting Backend on 0.0.0.0:8000...
start "Backend" cmd /k "cd /d %~dp0backend && venv\Scripts\activate && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

timeout /t 3 /nobreak > nul

echo [2/2] Starting Frontend on 0.0.0.0:5173...
start "Frontend" cmd /k "cd /d %~dp0frontend && npm run dev -- --host 0.0.0.0"

echo.
echo ========================================
echo  ProjectIQ - External Access
echo ========================================
echo  Local:    http://localhost:5173
echo  Network:  http://%LOCAL_IP%:5173
echo  Backend:  http://%LOCAL_IP%:8000
echo  API Docs: http://%LOCAL_IP%:8000/docs
echo ========================================
echo.
echo Share the Network URL with others on your Wi-Fi/LAN.
echo For internet access, run: start-tunnel.bat
echo.
pause
