@echo off
echo =========================================
echo Starting Sheet Music Finder
echo =========================================

echo 1. Setting up Python virtual environment...
cd backend
if not exist "venv" (
    python -m venv venv
)
call venv\Scripts\activate.bat

echo 2. Installing requirements...
pip install -r requirements.txt

echo 3. Starting FastAPI backend server...
start /B cmd /c "uvicorn app:app --reload --host 127.0.0.1 --port 8000"

echo 4. Starting frontend server...
cd ../frontend
start /B cmd /c "python -m http.server 3000"

echo.
echo =========================================
echo App is running!
echo Frontend: http://localhost:3000
echo Backend:  http://127.0.0.1:8000
echo =========================================
start http://localhost:3000
echo Press any key to terminate servers and exit.
pause > nul

echo Shutting down servers...
taskkill /F /IM python.exe /T > nul 2>&1
taskkill /F /IM uvicorn.exe /T > nul 2>&1
echo Done.
