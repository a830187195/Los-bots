"""Renderizador de pictogramas vectoriales accesibles sobre Kivy Canvas."""

from __future__ import annotations

from kivy.graphics import Color, Ellipse, Line, RoundedRectangle  # type: ignore import-not-found
from kivy.metrics import dp  # type: ignore import-not-found
from kivy.uix.widget import Widget  # type: ignore import-not-found

from src.layer1_presentation.theme import AccessibleTheme


class PictogramWidget(Widget):
    """Dibuja pictogramas vectoriales de alto contraste sin pérdida de resolución."""

    def __init__(
        self,
        theme: AccessibleTheme,
        pictogram_id: str = "documents",
        size_dp: int = 88,
        **kwargs: object,
    ) -> None:
        super().__init__(**kwargs)
        self._theme = theme
        self._pictogram_id = pictogram_id
        self.size_hint = (None, None)
        self.size = (dp(size_dp), dp(size_dp))
        self.bind(pos=self._redraw, size=self._redraw)
        self._redraw()

    def set_pictogram(self, pictogram_id: str) -> None:
        """Cambia el pictograma dibujado de forma instantánea."""
        self._pictogram_id = pictogram_id
        self._redraw()

    def _redraw(self, *_args: object) -> None:
        self.canvas.clear()
        x, y = self.pos
        w, h = self.size
        if w <= 0 or h <= 0:
            return

        pid = self._pictogram_id
        with self.canvas:
            # Tarjeta base suave para destacar el pictograma
            Color(*self._theme.surface_tinted)
            RoundedRectangle(pos=(x, y), size=(w, h), radius=[dp(18)])

            if pid in {"documents", "document_acta", "document_curp", "document_ine", "document_imss", "document_official", "document_generic", "document_home"}:
                self._draw_documents(x, y, w, h)
            elif pid in {"office_map", "map"}:
                self._draw_office_map(x, y, w, h)
            elif pid in {"window_officer", "steps"}:
                self._draw_officer_window(x, y, w, h)
            elif pid in {"payment"}:
                self._draw_payment(x, y, w, h)
            elif pid in {"check_done"}:
                self._draw_check_done(x, y, w, h)
            elif pid in {"language", "translator"}:
                self._draw_language(x, y, w, h)
            elif pid in {"offline"}:
                self._draw_offline(x, y, w, h)
            else:
                self._draw_documents(x, y, w, h)

    def _draw_documents(self, x: float, y: float, w: float, h: float) -> None:
        Color(*self._theme.surface_card)
        RoundedRectangle(
            pos=(x + w * 0.18, y + h * 0.22),
            size=(w * 0.52, h * 0.64),
            radius=[dp(8)],
        )
        Color(*self._theme.primary_blue)
        Line(
            rounded_rectangle=(x + w * 0.18, y + h * 0.22, w * 0.52, h * 0.64, dp(8)),
            width=dp(2.2),
        )
        Color(*self._theme.surface_card)
        RoundedRectangle(
            pos=(x + w * 0.30, y + h * 0.14),
            size=(w * 0.52, h * 0.64),
            radius=[dp(8)],
        )
        Color(*self._theme.brand_olive)
        Line(
            rounded_rectangle=(x + w * 0.30, y + h * 0.14, w * 0.52, h * 0.64, dp(8)),
            width=dp(2.4),
        )
        Color(*self._theme.primary_blue)
        Line(points=[x + w * 0.40, y + h * 0.58, x + w * 0.72, y + h * 0.58], width=dp(2.2))
        Line(points=[x + w * 0.40, y + h * 0.44, x + w * 0.72, y + h * 0.44], width=dp(2.2))
        Line(points=[x + w * 0.40, y + h * 0.30, x + w * 0.62, y + h * 0.30], width=dp(2.2))

    def _draw_office_map(self, x: float, y: float, w: float, h: float) -> None:
        Color(*self._theme.primary_blue)
        Line(
            points=[
                x + w * 0.16, y + h * 0.24,
                x + w * 0.16, y + h * 0.76,
                x + w * 0.44, y + h * 0.84,
                x + w * 0.66, y + h * 0.72,
                x + w * 0.84, y + h * 0.80,
                x + w * 0.84, y + h * 0.28,
                x + w * 0.66, y + h * 0.20,
                x + w * 0.44, y + h * 0.30,
                x + w * 0.16, y + h * 0.24,
            ],
            width=dp(2.2),
        )
        Color(*self._theme.brand_olive)
        Ellipse(pos=(x + w * 0.38, y + h * 0.48), size=(w * 0.24, h * 0.24))
        Line(points=[x + w * 0.50, y + h * 0.48, x + w * 0.50, y + h * 0.30], width=dp(3.0))

    def _draw_officer_window(self, x: float, y: float, w: float, h: float) -> None:
        Color(*self._theme.brand_olive)
        Ellipse(pos=(x + w * 0.36, y + h * 0.54), size=(w * 0.28, h * 0.28))
        Color(*self._theme.primary_blue)
        RoundedRectangle(
            pos=(x + w * 0.24, y + h * 0.22),
            size=(w * 0.52, h * 0.28),
            radius=[dp(12)],
        )
        Color(*self._theme.surface_card)
        RoundedRectangle(
            pos=(x + w * 0.16, y + h * 0.16),
            size=(w * 0.68, h * 0.12),
            radius=[dp(4)],
        )
        Color(*self._theme.primary_blue)
        Line(
            rounded_rectangle=(x + w * 0.16, y + h * 0.16, w * 0.68, h * 0.12, dp(4)),
            width=dp(2.0),
        )

    def _draw_payment(self, x: float, y: float, w: float, h: float) -> None:
        Color(*self._theme.warning_bg)
        RoundedRectangle(
            pos=(x + w * 0.14, y + h * 0.24),
            size=(w * 0.72, h * 0.52),
            radius=[dp(10)],
        )
        Color(*self._theme.primary_blue)
        Line(
            rounded_rectangle=(x + w * 0.14, y + h * 0.24, w * 0.72, h * 0.52, dp(10)),
            width=dp(2.4),
        )
        Color(*self._theme.brand_olive)
        Ellipse(pos=(x + w * 0.36, y + h * 0.36), size=(w * 0.28, h * 0.28))

    def _draw_check_done(self, x: float, y: float, w: float, h: float) -> None:
        Color(*self._theme.success_bg)
        Ellipse(pos=(x + w * 0.14, y + h * 0.14), size=(w * 0.72, h * 0.72))
        Color(*self._theme.success_fg)
        Line(ellipse=(x + w * 0.14, y + h * 0.14, w * 0.72, h * 0.72), width=dp(2.8))
        Line(
            points=[
                x + w * 0.30, y + h * 0.48,
                x + w * 0.45, y + h * 0.33,
                x + w * 0.70, y + h * 0.64,
            ],
            width=dp(3.8),
            cap="round",
            joint="round",
        )

    def _draw_language(self, x: float, y: float, w: float, h: float) -> None:
        Color(*self._theme.primary_blue)
        RoundedRectangle(
            pos=(x + w * 0.16, y + h * 0.42),
            size=(w * 0.44, h * 0.38),
            radius=[dp(10)],
        )
        Color(*self._theme.brand_olive)
        RoundedRectangle(
            pos=(x + w * 0.40, y + h * 0.18),
            size=(w * 0.44, h * 0.38),
            radius=[dp(10)],
        )

    def _draw_offline(self, x: float, y: float, w: float, h: float) -> None:
        Color(*self._theme.primary_blue)
        Line(ellipse=(x + w * 0.18, y + h * 0.18, w * 0.64, h * 0.64), width=dp(2.6))
        Line(points=[x + w * 0.50, y + h * 0.72, x + w * 0.50, y + h * 0.34], width=dp(3.0))
        Line(
            points=[
                x + w * 0.34, y + h * 0.48,
                x + w * 0.50, y + h * 0.32,
                x + w * 0.66, y + h * 0.48,
            ],
            width=dp(3.0),
        )
