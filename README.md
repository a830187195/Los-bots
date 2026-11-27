# Mi Trámite Justo — Equipo *Los bots*

Plataforma inclusiva **Offline-First** para democratizar el acceso a trámites oficiales en México (con foco inicial en Puebla), disponible en **3 formatos listos para ejecutar y distribuir**:

1. **Aplicación Python de Escritorio y Ejecutable Windows (`MiTramiteJusto.exe`)** — `main.py`, `MiTramiteJusto.spec`, `ejecutar_app.bat`, `compilar_ejecutable_exe.bat`.
2. **Aplicación Móvil Android Instalable (`.apk`)** — `buildozer.spec` + compilación automática en `.github/workflows/build-apk.yml`.
3. **Web PWA Estática Offline-First para GitHub Pages** — `web_pwa/` + `abrir_pwa_web.bat` + despliegue automático en `.github/workflows/deploy.yml`.

> **Manual completo paso a paso (instalables Windows, uso en Antigravity y subida a GitHub):** consulta [MANUAL_INSTALACION_Y_GITHUB.md](MANUAL_INSTALACION_Y_GITHUB.md).

---

## Inicio Rápido

### 1. Probar en 1 clic sin instalar nada (Web PWA)
Haz doble clic en **`abrir_pwa_web.bat`** (o abre `web_pwa/index.html` en Chrome/Edge).

### 2. Instalar entorno Python, correr pruebas y abrir app Python
```bat
instalar_dependencias.bat
ejecutar_app.bat
```

### 3. Generar ejecutable standalone para Windows (`.exe`)
```bat
compilar_ejecutable_exe.bat
```
El ejecutable final se crea en `dist\MiTramiteJusto.exe`.

### 4. Subir a GitHub y compilar `.apk`, `.exe` y GitHub Pages en la nube
Consulta la **Parte 3 y Parte 4** de [MANUAL_INSTALACION_Y_GITHUB.md](MANUAL_INSTALACION_Y_GITHUB.md).

---

## Arquitectura en 4 Capas y Módulos

| Capa / Carpeta | Responsabilidad |
|---|---|
| `src/domain/` | Modelos de dominio (`WorkflowFSM`, `DocumentAnalysisResult`, `LanguagePack`, `OfflinePackageManifest`) y contratos abstractos. |
| `src/layer1_presentation/` | Interfaz accesible **WCAG AAA** (`#4F634B`, `#FDFBF7`, `#1E3A5F`), botones `>= 56dp`, escala `A-`/`A+`, pictogramas en Canvas y lectura por voz. |
| `src/layer2_edge_ai/` | Motor FSM (`fsm_engine.py`), privacidad y redacción PII en RAM (`privacy.py`), OCR local (`ocr_pipeline.py`), simplificador burocrático (`document_interpreter.py`) y traductor dual (`translation_engine.py`). |
| `src/layer3_persistence/` | Llave segura (`keystore.py`), SQLite/SQLCipher AES-256-GCM (`database.py`), paquetes `.mtjpack` SHA-256 + Delta (`package_manager.py`) y cola con backoff exponencial (`sync_queue.py`). |
| `src/layer4_cloud/` y `src/platform_android/` | Cliente TLS 1.3 con Certificate Pinning y puentes Android (`TextToSpeech`, `RecognizerIntent`, `MediaPlayer`, Cámara, Conectividad y ML Kit). |
| `web_pwa/` | Versión Web PWA 100% estática con Service Worker (`sw.js`), `IndexedDB`, `<canvas>` local, Web Speech API y navegación por hash (`#home`, `#translator`, `#scanner`, `#offline`, `#guide`). |
| `assets/` | Logotipo oficial, paquetes lingüísticos desacoplados (`nah_puebla.json`, `tot_sierra.json`), 4 trámites completos (`acta_nacimiento`, `curp_tramite`, `imss_afiliacion`, `pension_adulto_mayor`) y pictogramas SVG. |
| `tests/` | Suite unitaria e integración (`pytest -v`). |
