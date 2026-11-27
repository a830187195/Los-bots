@echo off
title Mi Tramite Justo - Instalador de Dependencias
cd /d "%~dp0"
echo Iniciando instalacion de entorno Python para Mi Tramite Justo...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\setup_windows.ps1"
if errorlevel 1 (
    echo.
    echo [AVISO] La instalacion requiere revisar el mensaje anterior.
    pause
    exit /b 1
)
echo.
pause
