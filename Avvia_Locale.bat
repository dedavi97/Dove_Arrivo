@echo off
rem Apre il sito sul computer: http://localhost:8765 (chiudi questa finestra per fermarlo).
chcp 65001 >nul
cd /d "%~dp0"
where python >nul 2>nul
if errorlevel 1 (
    echo Python non trovato. Installalo da https://www.python.org e riprova.
    pause
    exit /b 1
)
start "" http://localhost:8765/
python -m scanner.servi_locale 8765
