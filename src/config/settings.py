"""Configuración global de arquitectura, tokens de accesibilidad y límites SLA."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Final

ROOT_DIR: Final[Path] = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class AppPaths:
    """Rutas relativas al paquete para activos y almacenamiento local."""

    root_dir: Path = ROOT_DIR
    assets_dir: Path = ROOT_DIR / "assets"
    branding_logo: Path = ROOT_DIR / "assets" / "branding" / "logo.jpeg"
    languages_dir: Path = ROOT_DIR / "assets" / "languages"
    packs_dir: Path = ROOT_DIR / "assets" / "packs"
    svg_dir: Path = ROOT_DIR / "assets" / "svg"


APP_PATHS: Final[AppPaths] = AppPaths()


@dataclass(frozen=True)
class SLATargets:
    """Objetivos no funcionales de rendimiento definidos en la arquitectura."""

    max_cold_start_seconds: float = 1.8
    max_apk_size_mb: float = 42.0
    max_runtime_ram_mb: float = 150.0
    audio_sample_rate_hz: int = 16000
    opus_bitrate_kbps: int = 20
    cloud_request_timeout_seconds: float = 3.5


SLA_TARGETS: Final[SLATargets] = SLATargets()


@dataclass(frozen=True)
class AccessibilityTokens:
    """Paleta WCAG AAA (>7:1 texto normal) y métricas táctiles mínimas."""

    # Colores de identidad de marca (Mi Trámite Justo)
    bg_cream: str = "#FDFBF7"
    surface_card: str = "#FFFFFF"
    surface_tinted: str = "#F2EFE9"
    brand_olive: str = "#4F634B"
    brand_olive_dark: str = "#354532"
    primary_blue: str = "#1E3A5F"
    primary_blue_dark: str = "#132640"

    # Alto contraste WCAG AAA sobre fondo crema (#FDFBF7) o blanco (#FFFFFF)
    text_primary: str = "#111827"      # Contraste > 15:1
    text_secondary: str = "#2D3748"    # Contraste > 10:1
    text_on_dark: str = "#FFFFFF"      # Contraste > 10:1 sobre #1E3A5F y #4F634B

    # Estados semánticos accesibles
    success_bg: str = "#DCFCE7"
    success_fg: str = "#14532D"
    warning_bg: str = "#FEF3C7"
    warning_fg: str = "#78350F"
    error_bg: str = "#FEE2E2"
    error_fg: str = "#7F1D1D"
    border_subtle: str = "#CBD5E1"
    border_strong: str = "#1E3A5F"

    # Métricas táctiles y tipográficas
    min_touch_dp: int = 56
    card_gap_dp: int = 16
    base_font_sp: int = 18
    title_font_sp: int = 24
    max_font_scale: float = 1.5
    min_font_scale: float = 0.9


ACCESSIBILITY_TOKENS: Final[AccessibilityTokens] = AccessibilityTokens()


@dataclass
class AppConfig:
    """Configuración mutable de tiempo de ejecución para almacenamiento y nube."""

    storage_dir: Path = field(default_factory=lambda: ROOT_DIR / ".local_data")
    gateway_base_url: str = "https://api.mitramitejusto.gob.mx.invalid/v1"
    pinned_cert_sha256: str = (
        "sha256/47DEQpj8HBSa+/TImW+5JCeuQeRkm5NMpJWZG3hSuFU="
    )
    allow_cloud_sync: bool = False  # Offline-First por defecto hasta habilitar red
    preferred_language: str = "nah_puebla"
    font_scale: float = 1.0
    high_contrast: bool = True
    auto_speak_steps: bool = False

    @property
    def db_path(self) -> Path:
        """Ruta al archivo de base de datos cifrada SQLite."""
        return self.storage_dir / "mitramitejusto.db"

    @property
    def installed_packs_dir(self) -> Path:
        """Directorio local donde se instalan paquetes .mtjpack verificados."""
        return self.storage_dir / "installed_packs"
