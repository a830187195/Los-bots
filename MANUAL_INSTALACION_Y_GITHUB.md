# Manual Paso a Paso: Instalación, Ejecución y Subida a GitHub ("Mi Trámite Justo")

Este manual explica **todo lo que debe tener instalado tu equipo** (Windows) para probar, ejecutar y empaquetar **Mi Trámite Justo** desde **Antigravity**, además de los pasos exactos para subir todo el proyecto a **GitHub**, generar el **`.exe`**, compilar el **`.apk` de Android** y publicar la **Web PWA en GitHub Pages**.

---

## Parte 1: Qué se debe instalar en el equipo (Windows)

Para trabajar cómodamente con el proyecto en Python y GitHub, instala estos **3 programas base** (en orden):

### 1. Python 3.11 (Obligatorio para la app Python, `.exe` y pruebas)
> **Nota importante de Windows:** Windows incluye un acceso directo falso en `WindowsApps\python.exe` que abre la Microsoft Store y da error de acceso si no has instalado Python real.

1. Descarga **Python 3.11 (64-bit)** desde:
   - Web oficial: `https://www.python.org/downloads/release/python-3119/` (baja *Windows installer (64-bit)*)
   - O desde PowerShell ejecutando:
     ```powershell
     winget install -e --id Python.Python.3.11
     ```
2. **MUY IMPORTANTE durante la instalación gráfica:**
   - Marca la casilla **"Add python.exe to PATH"** en la primera pantalla antes de pulsar *Install Now*.
3. *(Opcional si Windows sigue abriendo la Microsoft Store)*: Abre **Configuración de Windows → Aplicaciones → Configuración avanzada de aplicaciones → Alias de ejecución de aplicaciones** y desactiva `python.exe` y `python3.exe`.
4. Verifica en una terminal nueva de Antigravity:
   ```powershell
   python --version
   python -m pip --version
   ```

### 2. Git para Windows (Obligatorio para subir a GitHub)
1. Descarga e instala desde: `https://git-scm.com/download/win`
   - O con PowerShell:
     ```powershell
     winget install -e --id Git.Git
     ```
2. Deja las opciones por defecto y verifica en una terminal nueva:
   ```powershell
   git --version
   ```

### 3. Microsoft Visual C++ Redistributable (Solo si Kivy lo solicita al abrir en Windows)
- Si al abrir la ventana de Kivy aparece un error de DLL (`vcruntime140.dll`), descarga e instala el paquete oficial de Microsoft:
  `https://aka.ms/vs/17/release/vc_redist.x64.exe`

### 4. Instalables opcionales según lo que quieras compilar localmente
| Objetivo | ¿Necesitas instalar algo extra en Windows? | Alternativa sin instalar nada en Windows |
|---|---|---|
| **Probar la Web PWA ahora mismo** | **Nada.** Solo doble clic en `abrir_pwa_web.bat` (usa Edge/Chrome). | GitHub Pages lo publica automáticamente. |
| **Ejecutar la app Python en escritorio** | Solo Python 3.11 + doble clic en `instalar_dependencias.bat` y `ejecutar_app.bat`. | — |
| **Crear ejecutable `MiTramiteJusto.exe`** | Solo ejecutar `compilar_ejecutable_exe.bat` (instala PyInstaller en `.venv`). | GitHub Actions (`build-windows-exe.yml`) lo compila solo. |
| **Crear `.apk` de Android** | Requiere Linux o **WSL2 + Ubuntu 22.04 + OpenJDK 17 + Buildozer** (`wsl --install -d Ubuntu-22.04`). | **Recomendado:** GitHub Actions (`build-apk.yml`) compila el `.apk` gratis en la nube. |

---

## Parte 2: Cómo probar la aplicación paso a paso en tu equipo

### Opción A — Prueba inmediata sin instalar nada (Web PWA)
1. En la carpeta del proyecto, haz **doble clic en `abrir_pwa_web.bat`** (o abre `index.html` en Chrome/Edge).
2. Podrás probar los 4 módulos: **Lenguas Originarias**, **Leer Documento**, **Modo Sin Conexión** y **Guía Paso a Paso**.

### Opción B — Ejecutar la aplicación Python nativa (Kivy)
1. Haz doble clic en **`instalar_dependencias.bat`**.
   - Este script verifica Python 3.11, crea el entorno aislado `.venv`, actualiza `pip`, instala `kivy`, `pillow`, `cryptography`, `plyer`, `pytest`, `ruff`, `pyinstaller`, genera los paquetes `.mtjpack` y corre todas las pruebas unitarias.
2. Cuando termine, haz doble clic en **`ejecutar_app.bat`** (o ejecuta `.venv\Scripts\python.exe main.py` en la terminal de Antigravity).

### Opción C — Generar el ejecutable standalone `MiTramiteJusto.exe`
1. Con el entorno instalado, haz doble clic en **`compilar_ejecutable_exe.bat`**.
2. Al terminar, encontrarás el archivo ejecutable en:
   `dist\MiTramiteJusto.exe`
3. Ese `.exe` se puede copiar y ejecutar en cualquier equipo Windows sin necesidad de instalar Python ni dependencias.

---

## Parte 3: Cómo subir el proyecto a GitHub paso a paso

Ya se incluyeron todos los archivos necesarios para GitHub (`.gitignore`, `.gitattributes`, `LICENSE`, `CONTRIBUTING.md`, plantillas de Issues/PR y 3 flujos en `.github/workflows/`).

### 1. Crear el repositorio en GitHub
1. Entra a [github.com](https://github.com) e inicia sesión (con tu cuenta o GitHub Education).
2. Haz clic en **New repository** (`+` arriba a la derecha).
3. Ponle nombre (ejemplo: `mi-tramite-justo`), elige **Private** (si usan GitHub Education) o **Public**, y **NO** marques *Add a README* ni *.gitignore* (porque ya los tenemos creados).
4. Copia la URL HTTPS del repositorio (ejemplo: `https://github.com/tu-usuario/mi-tramite-justo.git`).

### 2. Inicializar Git y subir todo desde la terminal de Antigravity
Abre la terminal dentro de `C:\Users\Ivanna\Desktop\Hackaton` y ejecuta estos comandos en orden:

```powershell
# 1. Configurar tu identidad (solo la primera vez en este equipo)
git config --global user.name "Tu Nombre"
git config --global user.email "tu-correo@ejemplo.com"

# 2. Inicializar repositorio en la carpeta del proyecto
git init
git branch -M main

# 3. Verificar qué archivos se subirán (.gitignore excluye .venv, dist, .local_data, etc.)
git status

# 4. Agregar todos los archivos y hacer el primer commit
git add .
git commit -m "feat: arquitectura completa Mi Tramite Justo (Python APK/EXE + Web PWA)"

# 5. Conectar con tu repositorio remoto y subir
git remote add origin https://github.com/TU-USUARIO/mi-tramite-justo.git
git push -u origin main
```

---

## Parte 4: Activar los compiladores automáticos y GitHub Pages

Al hacer `git push`, GitHub ejecutará automáticamente **3 workflows** incluidos en `.github/workflows/`:

1. **Descargar el `.apk` instalable para Android (`build-apk.yml`):**
   - Ve a tu repositorio en GitHub → pestaña **Actions** → **Build Android APK (Mi Trámite Justo)**.
   - Cuando termine en verde, entra al resumen y descarga el archivo ZIP **`mi-tramite-justo-apk`** (contiene `mitramitejusto-1.0.0-arm64-v8a_armeabi-v7a-debug.apk`).
   - Pasa el `.apk` a tu celular Android y ábrelo para instalar (habilitando *"Instalar apps desconocidas"* si Android lo solicita).

2. **Descargar el `.exe` para Windows (`build-windows-exe.yml`):**
   - En la misma pestaña **Actions** → **Build Windows Executable (.exe)** → descarga **`mi-tramite-justo-windows-exe`**.

3. **Publicar la Web PWA en GitHub Pages (`index.html` en raíz o `deploy.yml`):**
   - En tu repositorio de GitHub ve a **Settings → Pages**.
   - En **Build and deployment → Source**, puedes elegir **Deploy from a branch** (`main` / `/ (root)`) directamente desde `index.html`, o **GitHub Actions** para usar `.github/workflows/deploy.yml`.
   - Vuelve a **Actions → Deploy Web PWA to GitHub Pages → Run workflow** (o haz un nuevo `git push`).
   - GitHub te dará el enlace público/privado (`https://tu-usuario.github.io/mi-tramite-justo/`) instalable desde Chrome en Android como PWA (*"Agregar a la pantalla principal"*).

---

## Parte 5: Solución rápida de problemas comunes

* **Error `'python' no se reconoce` o `El sistema no tiene acceso al archivo`:** Falta instalar Python 3.11 desde `python.org` marcando *"Add python.exe to PATH"* y reiniciar la terminal/Antigravity.
* **Error `'git' no se reconoce`:** Falta instalar Git para Windows y reiniciar la terminal/Antigravity.
* **La app Python falla al abrir ventana gráfica en Windows:** Instala `Microsoft Visual C++ Redistributable x64` o ejecuta `abrir_pwa_web.bat` mientras configuras los drivers gráficos.
* **El APK no compila en Windows nativo:** Buildozer solo compila Android en Linux/WSL2 o en GitHub Actions (`build-apk.yml`); usa el workflow automático de GitHub para obtener el `.apk` sin configurar Linux localmente.
