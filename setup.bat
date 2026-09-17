@echo off
echo Setting up ProjectIQ...
echo.

echo [1/4] Creating Python virtual environment...
cd backend
python -m venv venv
call venv\Scripts\activate
pip install -r requirements.txt
if not exist .env copy .env.example .env
cd ..

echo.
echo [2/4] Installing frontend dependencies...
cd frontend
call npm install
cd ..

echo.
echo ========================================
echo  Setup complete!
echo  Run start.bat to launch the application
echo ========================================
pause
