"""Puente nativo para captura de documentos mediante cámara o galería en Android/Desktop."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Callable

from src.domain.interfaces import CameraCapturePort


class PlatformCameraBridge(CameraCapturePort):
    """Solicita permisos Android en tiempo de ejecución y captura imágenes de documentos."""

    def capture_from_camera(self, on_captured: Callable[[str | None], None]) -> None:
        """Lanza cámara nativa en Android; en desktop solicita archivo o muestra ruta."""
        if _is_android_env():
            try:
                from android.permissions import Permission, request_permissions  # type: ignore import-not-found
                from plyer import camera  # type: ignore import-not-found

                def _after_perm(permissions: list[str], grants: list[bool]) -> None:
                    if not all(grants):
                        on_captured(None)
                        return
                    fd, tmp_path = tempfile.mkstemp(prefix="mtj_scan_", suffix=".jpg")
                    os.close(fd)
                    camera.take_picture(
                        filename=tmp_path,
                        on_complete=lambda path: on_captured(
                            path if path and Path(path).exists() else None
                        ),
                    )

                request_permissions([Permission.CAMERA], _after_perm)
                return
            except Exception:
                pass

        self.pick_from_gallery(on_captured)

    def pick_from_gallery(self, on_picked: Callable[[str | None], None]) -> None:
        """Abre el selector nativo de imágenes del sistema."""
        try:
            from plyer import filechooser  # type: ignore import-not-found

            filechooser.open_file(
                title="Selecciona fotografía del documento",
                filters=[("Imágenes", "*.png", "*.jpg", "*.jpeg", "*.webp")],
                on_selection=lambda sel: on_picked(sel[0] if sel else None),
            )
            return
        except Exception:
            on_picked(None)


def _is_android_env() -> bool:
    return "ANDROID_ARGUMENT" in os.environ or "ANDROID_PRIVATE" in os.environ
