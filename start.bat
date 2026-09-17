@echo off
echo Starting ProjectIQ...
echo.

echo [1/2] Starting Backend (FastAPI on port 8000)...
start "Backend" cmd /k "cd /d %~dp0backend && venv\Scripts\activate && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

timeout /t 3 /nobreak > nul

echo [2/2] Starting Frontend (Vite on port 5173)...
start "Frontend" cmd /k "cd /d %~dp0frontend && npm run dev -- --host 0.0.0.0"

echo.
echo ========================================
echo  ProjectIQ is starting!
echo  Backend:  http://localhost:8000
echo  Frontend: http://localhost:5173
echo  API Docs: http://localhost:8000/docs
echo  Logs:     backend\logs\app.log
echo ========================================
echo.
pause
