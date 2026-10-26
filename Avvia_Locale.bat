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
echo Sito in locale su http://localhost:8765
echo Per fermarlo chiudi questa finestra.
start "" http://localhost:8765/
python -m http.server 8765 --bind 127.0.0.1 --directory docs
