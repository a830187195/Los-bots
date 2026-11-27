"""Widgets reutilizables WCAG AAA con áreas táctiles >= 56dp y soporte de voz."""

from __future__ import annotations

from typing import Callable

from kivy.graphics import Color, Line, RoundedRectangle  # type: ignore import-not-found
from kivy.metrics import dp  # type: ignore import-not-found
from kivy.uix.boxlayout import BoxLayout  # type: ignore import-not-found
from kivy.uix.button import Button  # type: ignore import-not-found
from kivy.uix.label import Label  # type: ignore import-not-found
from kivy.uix.widget import Widget  # type: ignore import-not-found

from src.config.settings import ACCESSIBILITY_TOKENS
from src.domain.models import NetworkStatus
from src.layer1_presentation.theme import AccessibleTheme


class AccessibleLabel(Label):
    """Etiqueta multilínea autoajustable que nunca recorta texto al escalar fuentes."""

    def __init__(
        self,
        theme: AccessibleTheme,
        base_sp: int = ACCESSIBILITY_TOKENS.base_font_sp,
        color_rgba: tuple[float, float, float, float] | None = None,
        bold: bool = False,
        **kwargs: object,
    ) -> None:
        super().__init__(**kwargs)
        self._theme = theme
        self._base_sp = base_sp
        self.bold = bold
        self.color = color_rgba or theme.text_primary
        self.font_size = theme.sp_size(base_sp)
        self.size_hint_y = None
        if "halign" not in kwargs:
            self.halign = "left"
        if "valign" not in kwargs:
            self.valign = "top"
        self.bind(width=self._sync_text_width, texture_size=self._sync_height)
        theme.subscribe(self._refresh_font)

    def _sync_text_width(self, _inst: object, width: float) -> None:
        self.text_size = (max(dp(40), width - dp(4)), None)

    def _sync_height(self, _inst: object, tex_size: tuple[float, float]) -> None:
        self.height = max(dp(28), tex_size[1] + dp(8))

    def _refresh_font(self) -> None:
        self.font_size = self._theme.sp_size(self._base_sp)


class AccessibleButton(Button):
    """Botón de alto contraste con altura mínima obligatoria de 56dp y borde nítido."""

    def __init__(
        self,
        theme: AccessibleTheme,
        bg_rgba: tuple[float, float, float, float] | None = None,
        fg_rgba: tuple[float, float, float, float] | None = None,
        border_rgba: tuple[float, float, float, float] | None = None,
        base_sp: int = ACCESSIBILITY_TOKENS.base_font_sp,
        min_height_dp: int = ACCESSIBILITY_TOKENS.min_touch_dp,
        **kwargs: object,
    ) -> None:
        super().__init__(**kwargs)
        self._theme = theme
        self._base_sp = base_sp
        self._bg_rgba = bg_rgba or theme.primary_blue
        self.color = fg_rgba or theme.text_on_dark
        self._border_rgba = border_rgba or self._bg_rgba
        self.bold = True
        self.font_size = theme.sp_size(base_sp)
        self.background_normal = ""
        self.background_down = ""
        self.background_color = (0, 0, 0, 0)
        self.size_hint_y = None
        self.height = dp(max(ACCESSIBILITY_TOKENS.min_touch_dp, min_height_dp))
        self.halign = "center"
        self.valign = "middle"
        self.padding = (dp(14), dp(10))

        with self.canvas.before:
            self._bg_color_instr = Color(*self._bg_rgba)
            self._bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(14)])
            self._border_color_instr = Color(*self._border_rgba)
            self._border_line = Line(
                rounded_rectangle=(self.x, self.y, self.width, self.height, dp(14)),
                width=dp(1.6),
            )

        self.bind(pos=self._update_canvas, size=self._update_canvas, width=self._wrap_text)
        theme.subscribe(self._refresh_font)

    def set_colors(
        self,
        bg_rgba: tuple[float, float, float, float],
        fg_rgba: tuple[float, float, float, float],
        border_rgba: tuple[float, float, float, float] | None = None,
    ) -> None:
        """Actualiza colores manteniendo el contraste WCAG AAA."""
        self._bg_color_instr.rgba = bg_rgba
        self.color = fg_rgba
        self._border_color_instr.rgba = border_rgba or bg_rgba

    def _update_canvas(self, *_args: object) -> None:
        self._bg_rect.pos = self.pos
        self._bg_rect.size = self.size
        self._border_line.rounded_rectangle = (
            self.x,
            self.y,
            self.width,
            self.height,
            dp(14),
        )

    def _wrap_text(self, _inst: object, width: float) -> None:
        self.text_size = (max(dp(40), width - dp(24)), None)

    def _refresh_font(self) -> None:
        self.font_size = self._theme.sp_size(self._base_sp)


class SpeakerButton(AccessibleButton):
    """Botón universal de voz ('Escuchar') presente en toda pantalla y tarjeta."""

    def __init__(
        self,
        theme: AccessibleTheme,
        label_text: str = "Escuchar en voz alta",
        on_speak: Callable[[], None] | None = None,
        **kwargs: object,
    ) -> None:
        super().__init__(
            theme=theme,
            bg_rgba=theme.brand_olive,
            fg_rgba=theme.text_on_dark,
            border_rgba=theme.brand_olive,
            text=f"[Voz]  {label_text}",
            min_height_dp=56,
            **kwargs,
        )
        if on_speak is not None:
            self.bind(on_release=lambda *_a: on_speak())


class AccessibleCard(BoxLayout):
    """Contenedor de tarjeta con fondo claro, bordes definidos y espaciado generoso."""

    def __init__(
        self,
        theme: AccessibleTheme,
        bg_rgba: tuple[float, float, float, float] | None = None,
        border_rgba: tuple[float, float, float, float] | None = None,
        **kwargs: object,
    ) -> None:
        kwargs.setdefault("orientation", "vertical")
        kwargs.setdefault("padding", dp(16))
        kwargs.setdefault("spacing", dp(12))
        kwargs.setdefault("size_hint_y", None)
        super().__init__(**kwargs)

        bg = bg_rgba or theme.surface_card
        border = border_rgba or theme.border_subtle
        with self.canvas.before:
            self._bg_color = Color(*bg)
            self._bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(16)])
            self._bd_color = Color(*border)
            self._bd_line = Line(
                rounded_rectangle=(self.x, self.y, self.width, self.height, dp(16)),
                width=dp(1.4),
            )
        self.bind(pos=self._sync_rect, size=self._sync_rect)
        self.bind(minimum_height=self.setter("height"))

    def set_card_colors(
        self,
        bg_rgba: tuple[float, float, float, float],
        border_rgba: tuple[float, float, float, float],
    ) -> None:
        """Permite resaltar la tarjeta activa durante lectura o estado completado."""
        self._bg_color.rgba = bg_rgba
        self._bd_color.rgba = border_rgba

    def _sync_rect(self, *_args: object) -> None:
        self._bg_rect.pos = self.pos
        self._bg_rect.size = self.size
        self._bd_line.rounded_rectangle = (
            self.x,
            self.y,
            self.width,
            self.height,
            dp(16),
        )


class NetworkStatusPill(BoxLayout):
    """Indicador discreto y claro del estado de red (En línea / Sin conexión)."""

    def __init__(self, theme: AccessibleTheme) -> None:
        super().__init__(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(40),
            padding=(dp(12), dp(6)),
        )
        self._theme = theme
        with self.canvas.before:
            self._pill_color = Color(*theme.warning_bg)
            self._pill_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(12)])
        self.bind(pos=self._sync_bg, size=self._sync_bg)

        self._label = Label(
            text="Sin conexión · Modo local activo",
            color=theme.warning_fg,
            bold=True,
            font_size=theme.sp_size(14),
            halign="center",
            valign="middle",
        )
        self.add_widget(self._label)
        self.bind(width=lambda _i, w: setattr(self._label, "text_size", (w - dp(16), None)))

    def update_status(self, status: NetworkStatus) -> None:
        """Actualiza colores y texto ciudadano sin interrumpir con alertas."""
        if status == NetworkStatus.OFFLINE:
            self._pill_color.rgba = self._theme.warning_bg
            self._label.color = self._theme.warning_fg
            self._label.text = "Sin conexión · Funciona 100% en tu teléfono"
        elif status == NetworkStatus.ONLINE_WIFI:
            self._pill_color.rgba = self._theme.success_bg
            self._label.color = self._theme.success_fg
            self._label.text = "En línea (Wi-Fi) · Actualizaciones disponibles"
        else:
            self._pill_color.rgba = self._theme.success_bg
            self._label.color = self._theme.success_fg
            self._label.text = "En línea (Datos) · Modo ahorro activo"

    def _sync_bg(self, *_args: object) -> None:
        self._pill_rect.pos = self.pos
        self._pill_rect.size = self.size


class StepProgressBar(BoxLayout):
    """Barra de progreso visual clara para los pasos de la FSM."""

    def __init__(self, theme: AccessibleTheme) -> None:
        super().__init__(
            orientation="vertical",
            size_hint_y=None,
            height=dp(52),
            spacing=dp(6),
        )
        self._theme = theme
        self._ratio = 0.25

        self._label = AccessibleLabel(
            theme=theme,
            base_sp=16,
            bold=True,
            color_rgba=theme.primary_blue,
            text="Paso 1 de 4",
        )
        self._bar_canvas = Widget(size_hint_y=None, height=dp(16))
        with self._bar_canvas.canvas:
            Color(*theme.surface_tinted)
            self._track = RoundedRectangle(
                pos=self._bar_canvas.pos, size=self._bar_canvas.size, radius=[dp(8)]
            )
            Color(*theme.brand_olive)
            self._fill = RoundedRectangle(
                pos=self._bar_canvas.pos,
                size=(dp(40), dp(16)),
                radius=[dp(8)],
            )
        self._bar_canvas.bind(pos=self._redraw, size=self._redraw)
        self.add_widget(self._label)
        self.add_widget(self._bar_canvas)

    def set_progress(self, step_num: int, total_steps: int, ratio: float) -> None:
        """Actualiza etiqueta y barra de progreso."""
        self._ratio = max(0.05, min(1.0, ratio))
        self._label.text = f"Progreso: Paso {step_num} de {total_steps}"
        self._redraw()

    def _redraw(self, *_args: object) -> None:
        self._track.pos = self._bar_canvas.pos
        self._track.size = self._bar_canvas.size
        self._fill.pos = self._bar_canvas.pos
        self._fill.size = (
            max(dp(18), self._bar_canvas.width * self._ratio),
            self._bar_canvas.height,
        )
