@echo off
echo ===================================================
echo   Starting PM Copilot (Backend + Frontend)
echo ===================================================

echo Starting Backend Server on http://127.0.0.1:8000 ...
start "PM Copilot - FastAPI Backend" cmd /k "cd backend && .venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload"

echo Starting Frontend Server on http://localhost:5173 ...
start "PM Copilot - React Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo Both servers started in separate terminal windows!
echo Backend:  http://127.0.0.1:8000
echo Frontend: http://localhost:5173
echo.
pause
