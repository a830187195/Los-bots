@echo off
title Mi Tramite Justo - Ejecutar Aplicacion
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo [AVISO] Aun no se ha configurado el entorno virtual .venv.
    echo Ejecuta primero instalar_dependencias.bat con doble clic.
    pause
    exit /b 1
)
echo Abriendo Mi Tramite Justo...
".venv\Scripts\python.exe" main.py
if errorlevel 1 (
    echo.
    echo [ERROR] Ocurrio un problema al ejecutar la aplicacion.
    pause
)
