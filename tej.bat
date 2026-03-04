@echo off
REM TejStrike AI - Windows Quick Launcher
REM Double-click this to start TejStrike AI

echo Starting TejStrike AI...
cd /d "%~dp0"
python tej_ai.py %*
if errorlevel 1 (
    echo.
    echo Python not found or error occurred.
    echo Make sure Python 3.8+ is installed and in your PATH.
    pause
)
