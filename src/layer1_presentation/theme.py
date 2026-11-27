"""Gestor reactivo de tema accesible WCAG AAA y escalado tipográfico dinámico."""

from __future__ import annotations

from typing import Callable

from kivy.utils import get_color_from_hex  # type: ignore import-not-found

from src.config.settings import ACCESSIBILITY_TOKENS


class AccessibleTheme:
    """Controla colores de alto contraste y escala de fuente en tiempo real."""

    def __init__(self, initial_scale: float = 1.0, high_contrast: bool = True) -> None:
        self.font_scale = max(
            ACCESSIBILITY_TOKENS.min_font_scale,
            min(ACCESSIBILITY_TOKENS.max_font_scale, initial_scale),
        )
        self.high_contrast = high_contrast
        self._listeners: list[Callable[[], None]] = []

    def subscribe(self, callback: Callable[[], None]) -> None:
        """Registra vistas que deben re-escalar sus fuentes al pulsar A+ / A-."""
        if callback not in self._listeners:
            self._listeners.append(callback)

    def change_font_scale(self, delta: float) -> float:
        """Incrementa o reduce la escala tipográfica manteniendo límites legibles."""
        new_scale = round(self.font_scale + delta, 2)
        self.font_scale = max(
            ACCESSIBILITY_TOKENS.min_font_scale,
            min(ACCESSIBILITY_TOKENS.max_font_scale, new_scale),
        )
        for cb in list(self._listeners):
            cb()
        return self.font_scale

    def sp_size(self, base_sp: int) -> float:
        """Calcula tamaño tipográfico escalado listo para Kivy sp()."""
        from kivy.metrics import sp  # type: ignore import-not-found

        return float(sp(base_sp * self.font_scale))

    @staticmethod
    def rgba(hex_color: str) -> tuple[float, float, float, float]:
        """Convierte un token hexadecimal a tupla RGBA para Kivy canvas."""
        c = get_color_from_hex(hex_color)
        return (float(c[0]), float(c[1]), float(c[2]), float(c[3]))

    @property
    def bg_cream(self) -> tuple[float, float, float, float]:
        return self.rgba(ACCESSIBILITY_TOKENS.bg_cream)

    @property
    def surface_card(self) -> tuple[float, float, float, float]:
        return self.rgba(ACCESSIBILITY_TOKENS.surface_card)

    @property
    def surface_tinted(self) -> tuple[float, float, float, float]:
        return self.rgba(ACCESSIBILITY_TOKENS.surface_tinted)

    @property
    def brand_olive(self) -> tuple[float, float, float, float]:
        return self.rgba(ACCESSIBILITY_TOKENS.brand_olive)

    @property
    def primary_blue(self) -> tuple[float, float, float, float]:
        return self.rgba(ACCESSIBILITY_TOKENS.primary_blue)

    @property
    def text_primary(self) -> tuple[float, float, float, float]:
        return self.rgba(ACCESSIBILITY_TOKENS.text_primary)

    @property
    def text_secondary(self) -> tuple[float, float, float, float]:
        return self.rgba(ACCESSIBILITY_TOKENS.text_secondary)

    @property
    def text_on_dark(self) -> tuple[float, float, float, float]:
        return self.rgba(ACCESSIBILITY_TOKENS.text_on_dark)

    @property
    def success_bg(self) -> tuple[float, float, float, float]:
        return self.rgba(ACCESSIBILITY_TOKENS.success_bg)

    @property
    def success_fg(self) -> tuple[float, float, float, float]:
        return self.rgba(ACCESSIBILITY_TOKENS.success_fg)

    @property
    def warning_bg(self) -> tuple[float, float, float, float]:
        return self.rgba(ACCESSIBILITY_TOKENS.warning_bg)

    @property
    def warning_fg(self) -> tuple[float, float, float, float]:
        return self.rgba(ACCESSIBILITY_TOKENS.warning_fg)

    @property
    def border_strong(self) -> tuple[float, float, float, float]:
        return self.rgba(ACCESSIBILITY_TOKENS.border_strong)

    @property
    def border_subtle(self) -> tuple[float, float, float, float]:
        return self.rgba(ACCESSIBILITY_TOKENS.border_subtle)
