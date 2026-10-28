@echo off
title Karan AI Assistant - Launcher
cd /d "%~dp0"

echo ===================================================
echo     KARAN AI ASSISTANT - LAUNCHER
echo ===================================================
echo.

:: 1. Ensure Ollama is running
echo [1/3] Checking Ollama AI engine...
tasklist /fi "imagename eq ollama.exe" | find /i "ollama.exe" >nul
if errorlevel 1 (
    echo Starting Ollama background service...
    start "" /b ollama serve
    timeout /t 3 >nul
) else (
    echo Ollama is already running.
)

:: 2. Start Karan Python Web Server
echo.
echo [2/3] Starting Karan Flask Server on port 5000...
tasklist /fi "windowtitle eq KaranServer*" | find /i "cmd.exe" >nul
start "KaranServer" /min cmd /c "python server.py"
timeout /t 2 >nul

:: 3. Launch Custom Branded Public URL
echo.
echo [3/3] Starting Karan Public HTTPS Tunnel...
echo.
echo ===================================================
echo  1) Custom Branded URL:
echo     https://karan-ai-assistant.loca.lt
echo     (Tunnel Password if prompted on first visit: 106.76.70.129)
echo.
echo  2) Cloudflare High-Speed Tunnel:
echo     See Cloudflare URL below
echo ===================================================
echo.

:: Start Localtunnel in background
start "KaranLocaltunnel" /min cmd /c "npx -y localtunnel --port 5000 --subdomain karan-ai-assistant"

:: Run Cloudflare tunnel in foreground
cloudflared.exe tunnel --url http://127.0.0.1:5000
pause
