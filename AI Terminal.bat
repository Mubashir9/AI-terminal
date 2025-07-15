@echo off
title AI Command Assistant
color 0A

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python from https://python.org
    pause
    exit /b 1
)

REM Check if the Python script exists
if not exist "windows_ai_assistant.py" (
    echo ERROR: windows_ai_assistant.py not found
    echo Please make sure the script is in the same directory as this batch file
    pause
    exit /b 1
)

REM Check if Ollama is running
curl -s http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo Starting Ollama service...
    start /b ollama serve
    timeout /t 3 /nobreak >nul
)

REM Run the AI assistant
python windows_ai_assistant.py %*

REM Keep window open if there was an error
if errorlevel 1 (
    echo.
    echo Press any key to exit...
    pause >nul
)