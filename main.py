"""Punto de entrada principal requerido por Python-for-Android / Buildozer (main.py)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Asegura que el directorio raíz esté en sys.path tanto en Android APK como en Desktop
_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# Optimización para dispositivos Android de gama baja: desactivar logs ruidosos y reducir RAM
os.environ.setdefault("KIVY_NO_ARGS", "1")
if "ANDROID_ARGUMENT" in os.environ:
    os.environ.setdefault("KIVY_LOG_LEVEL", "warning")


def main() -> None:
    """Inicia la aplicación móvil Mi Trámite Justo."""
    from src.layer1_presentation.app import MiTramiteJustoApp

    MiTramiteJustoApp().run()


if __name__ == "__main__":
    main()
