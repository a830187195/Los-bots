[app]

# Nombre visible en el lanzador de Android
title = Mi Tramite Justo

# Nombre corto de paquete y dominio único
package.name = mitramitejusto
package.domain = org.losbots

# Código fuente en la raíz del proyecto
source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,json,svg,opus,ogg,wav,mtjpack
source.exclude_dirs = tests,.git,.github,.local_data,__pycache__,dist_packs,build,dist,.buildozer,.venv,web_pwa,docs,scripts

# Versión de la aplicación
version = 1.0.0

# Dependencias optimizadas para APK < 42 MB y RAM <= 150 MB
requirements = python3,kivy==2.3.0,pillow,cryptography,pyjnius,plyer

# Orientación y pantalla de carga con logotipo oficial
orientation = portrait
fullscreen = 0
icon.filename = %(source.dir)s/assets/branding/logo.png
presplash.filename = %(source.dir)s/assets/branding/logo.png
android.presplash_color = #FDFBF7

# Permisos Android mínimos necesarios (Principio de menor privilegio)
android.permissions = CAMERA,RECORD_AUDIO,INTERNET,ACCESS_NETWORK_STATE,READ_MEDIA_IMAGES,READ_EXTERNAL_STORAGE

# Soporte ARM64 y ARM32 para dispositivos de gama baja y media
android.archs = arm64-v8a, armeabi-v7a
android.api = 34
android.minapi = 24
android.ndk = 25b
android.accept_sdk_license = True

# Privacidad por diseño: deshabilitar respaldos automáticos en la nube de Android
android.allow_backup = False

# Opcional: descomentar para incluir Google ML Kit Text Recognition nativo en Gradle
# android.gradle_dependencies = com.google.mlkit:text-recognition:16.0.1

p4a.branch = master

[buildozer]
log_level = 2
warn_on_root = 1
