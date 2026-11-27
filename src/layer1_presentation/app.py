"""Orquestador principal de la aplicación Kivy con carga diferida (<1.8s cold start)."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from kivy.app import App  # type: ignore import-not-found
from kivy.core.window import Window  # type: ignore import-not-found
from kivy.uix.screenmanager import FadeTransition, ScreenManager  # type: ignore import-not-found

from src.config.settings import APP_PATHS, AppConfig
from src.layer1_presentation.screens.home_screen import HomeScreen
from src.layer1_presentation.theme import AccessibleTheme
from src.layer2_edge_ai.document_interpreter import DocumentInterpreter
from src.layer2_edge_ai.fsm_engine import WorkflowFSMEngine
from src.layer2_edge_ai.ocr_pipeline import LocalOCREngine
from src.layer2_edge_ai.translation_engine import DualTranslationEngine, LanguagePackRegistry
from src.layer3_persistence.database import EncryptedSQLiteRepository
from src.layer3_persistence.keystore import AndroidKeyStoreProvider
from src.layer3_persistence.package_manager import OfflinePackageManager
from src.layer3_persistence.sync_queue import SmartSyncQueue
from src.layer4_cloud.gateway_client import SecureCloudGatewayClient
from src.platform_android.audio_voice import PlatformAudioVoiceService
from src.platform_android.camera_bridge import PlatformCameraBridge
from src.platform_android.connectivity import PlatformConnectivityMonitor
from src.platform_android.mlkit_ocr import try_android_mlkit_ocr


class AppContainer:
    """Contenedor ligero de inyección de dependencias entre las 4 capas."""

    def __init__(self, config: AppConfig | None = None) -> None:
        self.config = config or self._resolve_default_config()
        self.keystore = AndroidKeyStoreProvider(self.config.storage_dir)
        master_key = self.keystore.get_or_create_master_key()

        self.repository = EncryptedSQLiteRepository(self.config.db_path, master_key)
        saved_lang = self.repository.load_preference("preferred_language", "")
        if saved_lang:
            self.config.preferred_language = saved_lang
        saved_scale = self.repository.load_preference("font_scale", "")
        if saved_scale:
            try:
                self.config.font_scale = float(saved_scale)
            except ValueError:
                pass

        self.connectivity = PlatformConnectivityMonitor(force_offline=False)
        self.audio_voice = PlatformAudioVoiceService()
        self.camera_bridge = PlatformCameraBridge()
        self.cloud_gateway = SecureCloudGatewayClient(
            base_url=self.config.gateway_base_url,
            pinned_cert_sha256=self.config.pinned_cert_sha256,
        )

        self.package_manager = OfflinePackageManager(
            bundled_packs_dir=APP_PATHS.packs_dir,
            installed_packs_dir=self.config.installed_packs_dir,
        )
        self.fsm_engine = WorkflowFSMEngine(repository=self.repository)
        self.lang_registry = LanguagePackRegistry()
        self.translator = DualTranslationEngine(
            registry=self.lang_registry,
            connectivity=self.connectivity,
            cloud_gateway=self.cloud_gateway,
            allow_cloud=self.config.allow_cloud_sync,
        )
        self.sync_queue = SmartSyncQueue(
            repository=self.repository,
            connectivity=self.connectivity,
        )

        # Módulos pesados inicializados bajo demanda para respetar <1.8s y <=150MB RAM
        self._ocr_engine: LocalOCREngine | None = None
        self._doc_interpreter: DocumentInterpreter | None = None

    @property
    def ocr_engine(self) -> LocalOCREngine:
        """Instancia diferida del motor OCR local."""
        if self._ocr_engine is None:
            hook = try_android_mlkit_ocr if _is_android() else None
            self._ocr_engine = LocalOCREngine(android_mlkit_hook=hook)
        return self._ocr_engine

    @property
    def doc_interpreter(self) -> DocumentInterpreter:
        """Instancia diferida del clasificador NER y simplificador ciudadano."""
        if self._doc_interpreter is None:
            self._doc_interpreter = DocumentInterpreter()
        return self._doc_interpreter

    @staticmethod
    def _resolve_default_config() -> AppConfig:
        if "ANDROID_PRIVATE" in os.environ:
            storage = Path(os.environ["ANDROID_PRIVATE"]) / "mtj_data"
            return AppConfig(storage_dir=storage)
        return AppConfig()


class MiTramiteJustoApp(App):
    """Aplicación Kivy instalable en Android APK bajo arquitectura Offline-First."""

    def __init__(self, container: AppContainer | None = None, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self.title = "Mi Trámite Justo"
        self.container = container or AppContainer()
        self.theme = AccessibleTheme(
            initial_scale=self.container.config.font_scale,
            high_contrast=self.container.config.high_contrast,
        )
        self._screen_manager: ScreenManager | None = None
        self._mounted_screens: set[str] = set()

    def build(self) -> ScreenManager:
        """Construye únicamente la pantalla de inicio para un arranque frío ultrarrápido."""
        if not _is_android():
            Window.size = (430, 820)
        if APP_PATHS.branding_logo.exists():
            self.icon = str(APP_PATHS.branding_logo)

        sm = ScreenManager(transition=FadeTransition(duration=0.12))
        home = HomeScreen(app_ref=self)
        sm.add_widget(home)
        self._mounted_screens.add("home")
        self._screen_manager = sm
        return sm

    def navigate_to(self, screen_name: str) -> None:
        """Monta bajo demanda la pantalla solicitada y navega sin bloquear la UI."""
        if self._screen_manager is None:
            return
        self.container.audio_voice.stop_audio()
        self._ensure_screen(screen_name)
        self._screen_manager.current = screen_name

    def open_guide_pack(self, pack_id: str) -> None:
        """Abre directamente la Guía Paso a Paso en el trámite especificado."""
        self._ensure_screen("guide")
        if self._screen_manager is not None:
            guide_screen: Any = self._screen_manager.get_screen("guide")
            guide_screen.load_pack(pack_id)
            self._screen_manager.current = "guide"

    def adjust_font_scale(self, delta: float) -> None:
        """Escala dinámicamente la tipografía y guarda la preferencia cifrada."""
        new_scale = self.theme.change_font_scale(delta)
        self.container.config.font_scale = new_scale
        self.container.repository.save_preference("font_scale", str(new_scale))

    def _ensure_screen(self, screen_name: str) -> None:
        if screen_name in self._mounted_screens or self._screen_manager is None:
            return
        if screen_name == "translator":
            from src.layer1_presentation.screens.translator_screen import TranslatorScreen

            self._screen_manager.add_widget(TranslatorScreen(app_ref=self))
        elif screen_name == "scanner":
            from src.layer1_presentation.screens.scanner_screen import ScannerScreen

            self._screen_manager.add_widget(ScannerScreen(app_ref=self))
        elif screen_name == "offline_hub":
            from src.layer1_presentation.screens.offline_hub_screen import OfflineHubScreen

            self._screen_manager.add_widget(OfflineHubScreen(app_ref=self))
        elif screen_name == "guide":
            from src.layer1_presentation.screens.guide_screen import GuideScreen

            self._screen_manager.add_widget(GuideScreen(app_ref=self))
        self._mounted_screens.add(screen_name)

    def on_stop(self) -> None:
        """Detiene audio activo y cierra limpiamente la base de datos SQLite cifrada."""
        self.container.audio_voice.stop_audio()
        self.container.repository.close()


def _is_android() -> bool:
    return "ANDROID_ARGUMENT" in os.environ or "ANDROID_PRIVATE" in os.environ
