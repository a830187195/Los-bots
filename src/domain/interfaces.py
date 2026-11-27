"""Contratos abstractos (Protocolos) para desacoplar infraestructura de negocio."""

from __future__ import annotations

from typing import Callable, Protocol

from src.domain.models import (
    NetworkStatus,
    OCRBoundingBox,
    OfflinePackageManifest,
    ProcedureProgress,
    SyncOperation,
    TranslationResult,
)


class KeyStorePort(Protocol):
    """Almacén seguro de llaves criptográficas (Android Keystore / Fallback)."""

    def get_or_create_master_key(self, alias: str = "mtj_master_aes256") -> bytes:
        """Recupera o genera de forma segura la llave maestra de 256 bits."""


class EncryptedRepositoryPort(Protocol):
    """Contrato de persistencia cifrada en reposo (Capa 3)."""

    def save_progress(self, progress: ProcedureProgress) -> None:
        """Persiste de forma atómica el estado actual de la FSM del usuario."""

    def load_progress(self, pack_id: str) -> ProcedureProgress | None:
        """Recupera el último estado guardado para un trámite."""

    def save_preference(self, key: str, value: str) -> None:
        """Guarda una preferencia de accesibilidad o idioma."""

    def load_preference(self, key: str, default: str = "") -> str:
        """Lee una preferencia persistida."""

    def enqueue_sync(self, operation: SyncOperation) -> None:
        """Encola una operación asíncrona para reconciliación con la nube."""


class OCRPort(Protocol):
    """Contrato para motores de extracción de texto local en dispositivo."""

    @property
    def backend_name(self) -> str:
        """Nombre identificador del motor activo."""

    def extract_text_boxes(
        self, image_bytes: bytes, hint_text: str | None = None
    ) -> list[OCRBoundingBox]:
        """Extrae bloques de texto desde bytes binarizados en memoria volátil."""


class AudioVoicePort(Protocol):
    """Subsistema unificado de voz (TTS, STT y reproducción Opus/WAV)."""

    def speak(self, text: str, lang_code: str = "es-MX") -> bool:
        """Sintetiza o narra en voz alta el texto especificado."""

    def play_audio_file(self, file_path: str) -> bool:
        """Reproduce un clip de audio pregrabado (.opus/.ogg/.wav)."""

    def stop_audio(self) -> None:
        """Detiene inmediatamente cualquier reproducción o síntesis activa."""

    def listen_once(
        self,
        lang_code: str,
        on_result: Callable[[str], None],
        on_error: Callable[[str], None],
    ) -> None:
        """Inicia captura de voz (ASR/STT) y notifica vía callbacks."""


class CameraCapturePort(Protocol):
    """Puente multiplataforma para captura de documento desde cámara o galería."""

    def capture_from_camera(self, on_captured: Callable[[str | None], None]) -> None:
        """Abre la cámara nativa y entrega la ruta temporal de imagen."""

    def pick_from_gallery(self, on_picked: Callable[[str | None], None]) -> None:
        """Permite seleccionar una imagen existente del dispositivo."""


class ConnectivityPort(Protocol):
    """Monitor no bloqueante del estado de conectividad del dispositivo."""

    def get_network_status(self) -> NetworkStatus:
        """Consulta el estado actual de red sin realizar bloqueos largos."""


class CloudGatewayPort(Protocol):
    """Contrato opcional hacia los microservicios en la nube (Capa 4)."""

    def translate_nmt(
        self, text: str, source_lang: str, target_lang: str
    ) -> TranslationResult | None:
        """Solicita inferencia NMT en nube; devuelve None si no hay red o falla."""

    def fetch_remote_manifest(self, pack_id: str) -> OfflinePackageManifest | None:
        """Consulta la última versión y hashes SHA-256 disponibles en CDN."""
