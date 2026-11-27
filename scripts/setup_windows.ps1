# Instalador automático de entorno para "Mi Trámite Justo" en Windows
# Ejecutar mediante: .\instalar_dependencias.bat

$ErrorActionPreference = "Stop"
Write-Host "==========================================================" -ForegroundColor Green
Write-Host "  Mi Tramite Justo - Instalador de Entorno Python (Windows)" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green

function Find-RealPython {
    $candidates = @()
    $cmdPy = Get-Command py -ErrorAction SilentlyContinue
    if ($cmdPy) { $candidates += "py -3.11"; $candidates += "py -3" }

    $commonPaths = @(
        "$env:LocalAppData\Programs\Python\Python311\python.exe",
        "$env:LocalAppData\Programs\Python\Python312\python.exe",
        "C:\Python311\python.exe",
        "C:\Python312\python.exe",
        "$env:ProgramFiles\Python311\python.exe",
        "$env:ProgramFiles\Python312\python.exe"
    )
    foreach ($p in $commonPaths) {
        if (Test-Path $p) { $candidates += $p }
    }

    $cmdPython = Get-Command python -ErrorAction SilentlyContinue
    if ($cmdPython -and ($cmdPython.Source -notmatch "WindowsApps")) {
        $candidates += $cmdPython.Source
    }

    foreach ($cand in $candidates) {
        try {
            if ($cand -like "py *") {
                $parts = $cand.Split(" ")
                $out = & $parts[0] $parts[1] -c "import sys; print(sys.executable)" 2>$null
            } else {
                $out = & $cand -c "import sys; print(sys.executable)" 2>$null
            }
            if ($LASTEXITCODE -eq 0 -and $out) {
                return $out.Trim()
            }
        } catch {}
    }
    return $null
}

$pythonExe = Find-RealPython
if (-not $pythonExe) {
    Write-Host "`n[1/5] No se detecto Python real instalado (el de WindowsApps es solo un acceso de Microsoft Store)." -ForegroundColor Yellow
    $winget = Get-Command winget -ErrorAction SilentlyContinue
    if ($winget) {
        Write-Host "Intentando instalar Python 3.11 automaticamente con winget..." -ForegroundColor Cyan
        winget install -e --id Python.Python.3.11 --accept-package-agreements --accept-source-agreements
        $pythonExe = Find-RealPython
    }
    if (-not $pythonExe) {
        Write-Host "`nPor favor instala Python 3.11 manualmente desde:" -ForegroundColor Red
        Write-Host "https://www.python.org/downloads/windows/" -ForegroundColor White
        Write-Host "IMPORTANTE: Marca la casilla 'Add python.exe to PATH' durante la instalacion." -ForegroundColor Yellow
        Write-Host "Despues vuelve a ejecutar instalar_dependencias.bat." -ForegroundColor Yellow
        exit 1
    }
}

Write-Host "[1/5] Python encontrado en: $pythonExe" -ForegroundColor Cyan

$rootDir = Split-Path -Parent $PSScriptRoot
Set-Location $rootDir

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "[2/5] Creando entorno virtual aislado (.venv)..." -ForegroundColor Cyan
    & $pythonExe -m venv .venv
} else {
    Write-Host "[2/5] Entorno virtual (.venv) ya existe." -ForegroundColor Cyan
}

$venvPy = Join-Path $rootDir ".venv\Scripts\python.exe"

Write-Host "[3/5] Actualizando pip e instalando dependencias de la app..." -ForegroundColor Cyan
& $venvPy -m pip install --upgrade pip
& $venvPy -m pip install -r requirements.txt
& $venvPy -m pip install pytest ruff pyinstaller

Write-Host "[4/5] Generando paquetes offline (.mtjpack)..." -ForegroundColor Cyan
& $venvPy scripts\build_packs.py

Write-Host "[5/5] Ejecutando pruebas unitarias para verificar instalacion..." -ForegroundColor Cyan
& $venvPy -m pytest -v

Write-Host "`n==========================================================" -ForegroundColor Green
Write-Host "  Instalacion completa!" -ForegroundColor Green
Write-Host "  -> Haz doble clic en 'ejecutar_app.bat' para abrir la app." -ForegroundColor White
Write-Host "  -> Haz doble clic en 'compilar_ejecutable_exe.bat' para crear el .exe." -ForegroundColor White
Write-Host "==========================================================" -ForegroundColor Green
