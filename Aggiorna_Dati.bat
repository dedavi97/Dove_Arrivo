@echo off
rem Scarica l'orario, ricostruisce docs\data\rete.json, mostra il riepilogo
rem e chiede se pubblicare (commit + push del solo file dati).
chcp 65001 >nul
cd /d "%~dp0"
where python >nul 2>nul
if errorlevel 1 (
    echo Python non trovato. Installalo da https://www.python.org e riprova.
    pause
    exit /b 1
)
python -m scanner
echo.
pause
