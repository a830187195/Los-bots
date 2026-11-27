"""Puentes nativos hacia hardware y APIs de Android (pyjnius / plyer) con fallback desktop."""

from src.platform_android.audio_voice import PlatformAudioVoiceService
from src.platform_android.camera_bridge import PlatformCameraBridge
from src.platform_android.connectivity import PlatformConnectivityMonitor
from src.platform_android.mlkit_ocr import try_android_mlkit_ocr

__all__ = [
    "PlatformAudioVoiceService",
    "PlatformCameraBridge",
    "PlatformConnectivityMonitor",
    "try_android_mlkit_ocr",
]
