@echo off
title Mi Tramite Justo - Compilar Ejecutable Windows (.exe)
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo [AVISO] Ejecuta primero instalar_dependencias.bat.
    pause
    exit /b 1
)
echo [1/2] Verificando PyInstaller...
".venv\Scripts\python.exe" -m pip install --upgrade pyinstaller
echo [2/2] Compilando ejecutable standalone MiTramiteJusto.exe...
".venv\Scripts\pyinstaller.exe" --clean --noconfirm MiTramiteJusto.spec
if errorlevel 1 (
    echo.
    echo [ERROR] Fallo la compilacion del ejecutable.
    pause
    exit /b 1
)
echo.
echo ==========================================================
echo   Ejecutable generado exitosamente en:
echo   %cd%\dist\MiTramiteJusto.exe
echo ==========================================================
pause
