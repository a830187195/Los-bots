"""Clase base compartida para pantallas con fondo crema WCAG AAA y barra superior accesible."""

from __future__ import annotations

from typing import TYPE_CHECKING

from kivy.graphics import Color, Rectangle  # type: ignore import-not-found
from kivy.metrics import dp  # type: ignore import-not-found
from kivy.uix.boxlayout import BoxLayout  # type: ignore import-not-found
from kivy.uix.screenmanager import Screen  # type: ignore import-not-found
from kivy.uix.scrollview import ScrollView  # type: ignore import-not-found

from src.layer1_presentation.widgets.accessible import (
    AccessibleButton,
    AccessibleLabel,
    NetworkStatusPill,
)

if TYPE_CHECKING:
    from src.layer1_presentation.app import MiTramiteJustoApp


class BaseAccessibleScreen(Screen):
    """Proporciona cabecera institucional, controles de texto A+/A- y desplazamiento seguro."""

    def __init__(
        self,
        app_ref: MiTramiteJustoApp,
        screen_title: str,
        show_back: bool = True,
        **kwargs: object,
    ) -> None:
        super().__init__(**kwargs)
        self.app_ref = app_ref
        self.theme = app_ref.theme

        with self.canvas.before:
            Color(*self.theme.bg_cream)
            self._bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._sync_bg, size=self._sync_bg)

        self.root_layout = BoxLayout(orientation="vertical")
        self.add_widget(self.root_layout)

        # Cabecera institucional de alto contraste
        header = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(68),
            padding=(dp(12), dp(8)),
            spacing=dp(8),
        )
        with header.canvas.before:
            Color(*self.theme.primary_blue)
            self._hdr_rect = Rectangle(pos=header.pos, size=header.size)
        header.bind(pos=self._sync_hdr, size=self._sync_hdr)

        if show_back:
            back_btn = AccessibleButton(
                theme=self.theme,
                bg_rgba=self.theme.brand_olive,
                fg_rgba=self.theme.text_on_dark,
                text="< Inicio",
                base_sp=15,
                min_height_dp=56,
                size_hint_x=None,
                width=dp(98),
            )
            back_btn.bind(on_release=lambda *_a: self.app_ref.navigate_to("home"))
            header.add_widget(back_btn)

        self.header_title = AccessibleLabel(
            theme=self.theme,
            base_sp=19,
            bold=True,
            color_rgba=self.theme.text_on_dark,
            text=screen_title,
            valign="middle",
        )
        self.header_title.size_hint_y = 1
        header.add_widget(self.header_title)

        btn_dec = AccessibleButton(
            theme=self.theme,
            bg_rgba=self.theme.surface_card,
            fg_rgba=self.theme.primary_blue,
            text="A-",
            base_sp=16,
            min_height_dp=56,
            size_hint_x=None,
            width=dp(56),
        )
        btn_dec.bind(on_release=lambda *_a: self.app_ref.adjust_font_scale(-0.1))

        btn_inc = AccessibleButton(
            theme=self.theme,
            bg_rgba=self.theme.surface_card,
            fg_rgba=self.theme.primary_blue,
            text="A+",
            base_sp=16,
            min_height_dp=56,
            size_hint_x=None,
            width=dp(56),
        )
        btn_inc.bind(on_release=lambda *_a: self.app_ref.adjust_font_scale(0.1))

        header.add_widget(btn_dec)
        header.add_widget(btn_inc)
        self.root_layout.add_widget(header)

        # Indicador de red persistente no intrusivo
        status_wrap = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=dp(52),
            padding=(dp(14), dp(6)),
        )
        self.network_pill = NetworkStatusPill(self.theme)
        status_wrap.add_widget(self.network_pill)
        self.root_layout.add_widget(status_wrap)

        # Área desplazable principal
        self.scroll = ScrollView(do_scroll_x=False, bar_width=dp(6))
        self.content_box = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            padding=(dp(16), dp(12)),
            spacing=dp(16),
        )
        self.content_box.bind(minimum_height=self.content_box.setter("height"))
        self.scroll.add_widget(self.content_box)
        self.root_layout.add_widget(self.scroll)

    def on_pre_enter(self, *_args: object) -> None:
        """Sincroniza indicador de red al entrar a cualquier pantalla."""
        self.refresh_network_banner()

    def refresh_network_banner(self) -> None:
        """Actualiza el estado de conectividad sin bloquear el hilo gráfico."""
        status = self.app_ref.container.connectivity.get_network_status()
        self.network_pill.update_status(status)

    def _sync_bg(self, *_args: object) -> None:
        self._bg_rect.pos = self.pos
        self._bg_rect.size = self.size

    def _sync_hdr(self, instance: BoxLayout, *_args: object) -> None:
        self._hdr_rect.pos = instance.pos
        self._hdr_rect.size = instance.size
