"""Pantalla Principal (Hub 2x2 de alto contraste inspirado en el esquema oficial)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from kivy.metrics import dp  # type: ignore import-not-found
from kivy.uix.boxlayout import BoxLayout  # type: ignore import-not-found
from kivy.uix.gridlayout import GridLayout  # type: ignore import-not-found
from kivy.uix.image import Image  # type: ignore import-not-found

from src.config.settings import APP_PATHS
from src.layer1_presentation.screens.base_screen import BaseAccessibleScreen
from src.layer1_presentation.widgets.accessible import (
    AccessibleButton,
    AccessibleCard,
    AccessibleLabel,
    SpeakerButton,
)
from src.layer1_presentation.widgets.pictograms import PictogramWidget

if TYPE_CHECKING:
    from src.layer1_presentation.app import MiTramiteJustoApp


class HomeScreen(BaseAccessibleScreen):
    """Menú principal visual con 4 módulos grandes, logo de marca y guía de voz."""

    def __init__(self, app_ref: MiTramiteJustoApp, **kwargs: object) -> None:
        super().__init__(
            app_ref=app_ref,
            screen_title="Mi Trámite Justo",
            show_back=False,
            name="home",
            **kwargs,
        )
        self._build_ui()

    def _build_ui(self) -> None:
        # Tarjeta de bienvenida con logo oficial Mi Trámite Justo
        brand_card = AccessibleCard(
            theme=self.theme,
            bg_rgba=self.theme.surface_card,
            border_rgba=self.theme.brand_olive,
            orientation="horizontal",
        )
        if APP_PATHS.branding_logo.exists():
            logo = Image(
                source=str(APP_PATHS.branding_logo),
                size_hint=(None, None),
                size=(dp(84), dp(84)),
                fit_mode="contain",
            )
            brand_card.add_widget(logo)

        intro_col = BoxLayout(orientation="vertical", spacing=dp(4), size_hint_y=None)
        intro_col.bind(minimum_height=intro_col.setter("height"))
        intro_col.add_widget(
            AccessibleLabel(
                theme=self.theme,
                base_sp=20,
                bold=True,
                color_rgba=self.theme.brand_olive,
                text="Tu guía clara para trámites oficiales",
            )
        )
        intro_col.add_widget(
            AccessibleLabel(
                theme=self.theme,
                base_sp=15,
                color_rgba=self.theme.text_secondary,
                text="Funciona sin internet. Toca un botón grande para empezar o pulsa Escuchar.",
            )
        )
        brand_card.add_widget(intro_col)
        self.content_box.add_widget(brand_card)

        # Botón universal de lectura en voz alta
        self.content_box.add_widget(
            SpeakerButton(
                theme=self.theme,
                label_text="Escuchar opciones de inicio",
                on_speak=self._speak_home_overview,
            )
        )

        # Cuadrícula 2x2 de módulos principales (Puente, Documento, Offline, Pasos)
        grid = GridLayout(
            cols=2,
            spacing=dp(16),
            size_hint_y=None,
        )
        grid.bind(minimum_height=grid.setter("height"))

        grid.add_widget(
            self._build_module_tile(
                title="1. Lenguas\nOriginarias",
                subtitle="Español ↔\nNáhuatl / Totonaco",
                pictogram_id="language",
                target_screen="translator",
            )
        )
        grid.add_widget(
            self._build_module_tile(
                title="2. Leer\nDocumento",
                subtitle="Explica papeles\nen palabras claras",
                pictogram_id="documents",
                target_screen="scanner",
            )
        )
        grid.add_widget(
            self._build_module_tile(
                title="3. Modo Sin\nConexión",
                subtitle="Guías guardadas\ny paquetes",
                pictogram_id="offline",
                target_screen="offline_hub",
            )
        )
        grid.add_widget(
            self._build_module_tile(
                title="4. Guía Paso\na Paso",
                subtitle="Acompañamiento\ninteractivo",
                pictogram_id="steps",
                target_screen="guide",
            )
        )
        self.content_box.add_widget(grid)

        # Acceso directo de emergencia / reanudación del último trámite
        self.resume_card = AccessibleCard(
            theme=self.theme,
            bg_rgba=self.theme.surface_tinted,
            border_rgba=self.theme.primary_blue,
        )
        self.resume_label = AccessibleLabel(
            theme=self.theme,
            base_sp=16,
            bold=True,
            color_rgba=self.theme.primary_blue,
            text="Acceso rápido: Reanudar Acta de Nacimiento o CURP",
        )
        self.resume_card.add_widget(self.resume_label)
        resume_btn = AccessibleButton(
            theme=self.theme,
            bg_rgba=self.theme.primary_blue,
            fg_rgba=self.theme.text_on_dark,
            text="Abrir Guía Paso a Paso",
            min_height_dp=56,
        )
        resume_btn.bind(on_release=lambda *_a: self.app_ref.navigate_to("guide"))
        self.resume_card.add_widget(resume_btn)
        self.content_box.add_widget(self.resume_card)

    def _build_module_tile(
        self,
        title: str,
        subtitle: str,
        pictogram_id: str,
        target_screen: str,
    ) -> AccessibleCard:
        card = AccessibleCard(
            theme=self.theme,
            bg_rgba=self.theme.surface_card,
            border_rgba=self.theme.primary_blue,
        )
        pic_wrap = BoxLayout(size_hint_y=None, height=dp(78))
        pic_wrap.add_widget(
            PictogramWidget(theme=self.theme, pictogram_id=pictogram_id, size_dp=72)
        )
        card.add_widget(pic_wrap)

        card.add_widget(
            AccessibleLabel(
                theme=self.theme,
                base_sp=17,
                bold=True,
                color_rgba=self.theme.primary_blue,
                text=title,
            )
        )
        card.add_widget(
            AccessibleLabel(
                theme=self.theme,
                base_sp=14,
                color_rgba=self.theme.text_secondary,
                text=subtitle,
            )
        )
        btn = AccessibleButton(
            theme=self.theme,
            bg_rgba=self.theme.primary_blue,
            fg_rgba=self.theme.text_on_dark,
            text="Abrir",
            base_sp=16,
            min_height_dp=56,
        )
        btn.bind(on_release=lambda *_a: self.app_ref.navigate_to(target_screen))
        card.add_widget(btn)
        return card

    def _speak_home_overview(self) -> None:
        self.app_ref.container.audio_voice.speak(
            "Bienvenido a Mi Trámite Justo. Tienes cuatro botones grandes: "
            "uno, Lenguas Originarias para traducir entre Español, Náhuatl y Totonaco; "
            "dos, Leer Documento para explicar papeles oficiales; "
            "tres, Modo Sin Conexión para descargar guías; "
            "y cuatro, Guía Paso a Paso para hacer tu trámite."
        )
