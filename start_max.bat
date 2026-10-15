@echo off
chcp 65001 >nul
title MAX AI Assistant
color 0B

echo.
echo  ========================================
echo       MAX AI Assistant - Setup
echo  ========================================
echo.

cd /d "%~dp0"

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERROR] Python is not installed!
    echo  Please install Python from https://python.org
    pause
    exit /b 1
)

:: Check if .env exists
if not exist ".env" (
    echo  [!] No .env file found. Creating from template...
    copy ".env.example" ".env" >nul
    echo  [!] Please edit .env and add your Groq API key!
    echo  [!] Get a FREE key at: https://console.groq.com
    echo.
    notepad ".env"
    pause
    exit /b 0
)

:: Install dependencies
echo  [*] Checking dependencies...
pip install -r requirements.txt -q

echo.
echo  [*] Starting Max...
echo  [*] Press Ctrl+C to stop
echo.

:: Run Max
python main.py

pause
