"""Módulo 1: Puente Lingüístico Bidireccional (Español ↔ Náhuatl / Totonaco)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from kivy.clock import Clock  # type: ignore import-not-found
from kivy.metrics import dp  # type: ignore import-not-found
from kivy.uix.boxlayout import BoxLayout  # type: ignore import-not-found
from kivy.uix.textinput import TextInput  # type: ignore import-not-found

from src.domain.models import LanguageEntry, TranslationResult
from src.layer1_presentation.screens.base_screen import BaseAccessibleScreen
from src.layer1_presentation.widgets.accessible import (
    AccessibleButton,
    AccessibleCard,
    AccessibleLabel,
    SpeakerButton,
)

if TYPE_CHECKING:
    from src.layer1_presentation.app import MiTramiteJustoApp


class TranslatorScreen(BaseAccessibleScreen):
    """Traducción por voz y texto con conmutación automática Online/Offline."""

    def __init__(self, app_ref: MiTramiteJustoApp, **kwargs: object) -> None:
        super().__init__(
            app_ref=app_ref,
            screen_title="Puente Lingüístico",
            show_back=True,
            name="translator",
            **kwargs,
        )
        self._selected_lang = self.app_ref.container.config.preferred_language
        self._es_to_indigenous = True
        self._last_result: TranslationResult | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        # Selector de lengua originaria desacoplado desde LanguagePackRegistry
        lang_card = AccessibleCard(theme=self.theme)
        lang_card.add_widget(
            AccessibleLabel(
                theme=self.theme,
                base_sp=17,
                bold=True,
                text="1. Elige tu lengua originaria y dirección:",
            )
        )
        lang_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(60), spacing=dp(12))
        self._lang_buttons: dict[str, AccessibleButton] = {}
        for pack in self.app_ref.container.lang_registry.list_packs():
            short_name = pack.display_name.split("(")[0].strip()
            btn = AccessibleButton(
                theme=self.theme,
                text=short_name,
                base_sp=16,
                min_height_dp=56,
            )
            code = pack.lang_code
            btn.bind(on_release=lambda _b, lc=code: self._select_language(lc))
            self._lang_buttons[code] = btn
            lang_row.add_widget(btn)
        lang_card.add_widget(lang_row)

        self._dir_btn = AccessibleButton(
            theme=self.theme,
            bg_rgba=self.theme.brand_olive,
            fg_rgba=self.theme.text_on_dark,
            text="Dirección: Español  -->  Náhuatl",
            base_sp=16,
            min_height_dp=56,
        )
        self._dir_btn.bind(on_release=lambda *_a: self._toggle_direction())
        lang_card.add_widget(self._dir_btn)
        self.content_box.add_widget(lang_card)

        # Entrada de texto + micrófono STT
        input_card = AccessibleCard(theme=self.theme)
        input_card.add_widget(
            AccessibleLabel(
                theme=self.theme,
                base_sp=17,
                bold=True,
                text="2. Escribe o dicta lo que deseas comunicar:",
            )
        )
        self.input_field = TextInput(
            text="Buenos días, vengo a mi trámite.",
            multiline=True,
            size_hint_y=None,
            height=dp(96),
            font_size=self.theme.sp_size(18),
            background_color=(1, 1, 1, 1),
            foreground_color=self.theme.text_primary,
            padding=(dp(12), dp(12)),
        )
        input_card.add_widget(self.input_field)

        action_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(60), spacing=dp(12))
        mic_btn = AccessibleButton(
            theme=self.theme,
            bg_rgba=self.theme.surface_tinted,
            fg_rgba=self.theme.primary_blue,
            border_rgba=self.theme.primary_blue,
            text="[Mic] Hablar",
            base_sp=16,
            min_height_dp=56,
        )
        mic_btn.bind(on_release=lambda *_a: self._start_voice_input())

        translate_btn = AccessibleButton(
            theme=self.theme,
            bg_rgba=self.theme.primary_blue,
            fg_rgba=self.theme.text_on_dark,
            text="Traducir ahora",
            base_sp=16,
            min_height_dp=56,
        )
        translate_btn.bind(on_release=lambda *_a: self._run_translation())
        action_row.add_widget(mic_btn)
        action_row.add_widget(translate_btn)
        input_card.add_widget(action_row)
        self.content_box.add_widget(input_card)

        # Tarjeta de resultado
        self.result_card = AccessibleCard(
            theme=self.theme,
            bg_rgba=self.theme.surface_card,
            border_rgba=self.theme.brand_olive,
        )
        self.result_engine_lbl = AccessibleLabel(
            theme=self.theme,
            base_sp=14,
            bold=True,
            color_rgba=self.theme.brand_olive,
            text="Traducción lista",
        )
        self.result_text_lbl = AccessibleLabel(
            theme=self.theme,
            base_sp=22,
            bold=True,
            color_rgba=self.theme.primary_blue,
            text="Niltze, nika' notlahtol",
        )
        self.result_phonetic_lbl = AccessibleLabel(
            theme=self.theme,
            base_sp=16,
            color_rgba=self.theme.text_secondary,
            text="Pronunciación: Nil-tse, ni-ka no-tlaj-tol",
        )
        self.result_note_lbl = AccessibleLabel(
            theme=self.theme,
            base_sp=14,
            color_rgba=self.theme.text_secondary,
            text="Nota: Datos demostrativos pendientes de validación comunitaria.",
        )
        self.result_card.add_widget(self.result_engine_lbl)
        self.result_card.add_widget(self.result_text_lbl)
        self.result_card.add_widget(self.result_phonetic_lbl)
        self.result_card.add_widget(self.result_note_lbl)
        self.result_card.add_widget(
            SpeakerButton(
                theme=self.theme,
                label_text="Escuchar traducción",
                on_speak=self._speak_translation,
            )
        )
        self.content_box.add_widget(self.result_card)

        # Frases rápidas listas para ventanilla
        phrases_card = AccessibleCard(theme=self.theme)
        phrases_card.add_widget(
            AccessibleLabel(
                theme=self.theme,
                base_sp=17,
                bold=True,
                text="Frases rápidas de ventanilla (toca para traducir):",
            )
        )
        self.phrases_box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(10))
        self.phrases_box.bind(minimum_height=self.phrases_box.setter("height"))
        phrases_card.add_widget(self.phrases_box)
        self.content_box.add_widget(phrases_card)

        self._refresh_language_ui()
        self._run_translation()

    def _select_language(self, lang_code: str) -> None:
        self._selected_lang = lang_code
        self.app_ref.container.config.preferred_language = lang_code
        self.app_ref.container.repository.save_preference("preferred_language", lang_code)
        self._refresh_language_ui()
        self._run_translation()

    def _toggle_direction(self) -> None:
        self._es_to_indigenous = not self._es_to_indigenous
        self._refresh_language_ui()

    def _refresh_language_ui(self) -> None:
        for code, btn in self._lang_buttons.items():
            if code == self._selected_lang:
                btn.set_colors(self.theme.primary_blue, self.theme.text_on_dark)
            else:
                btn.set_colors(
                    self.theme.surface_tinted,
                    self.theme.primary_blue,
                    self.theme.primary_blue,
                )

        pack = self.app_ref.container.lang_registry.get_pack(self._selected_lang)
        lang_name = pack.display_name.split("(")[0].strip() if pack else self._selected_lang
        if self._es_to_indigenous:
            self._dir_btn.text = f"Dirección: Español  -->  {lang_name}"
        else:
            self._dir_btn.text = f"Dirección: {lang_name}  -->  Español"

        self.phrases_box.clear_widgets()
        entries = self.app_ref.container.translator.search_quick_phrases(self._selected_lang)
        for entry in entries[:6]:
            self._add_phrase_button(entry)

    def _add_phrase_button(self, entry: LanguageEntry) -> None:
        text_shown = entry.spanish if self._es_to_indigenous else entry.indigenous_text
        btn = AccessibleButton(
            theme=self.theme,
            bg_rgba=self.theme.surface_tinted,
            fg_rgba=self.theme.text_primary,
            border_rgba=self.theme.border_subtle,
            text=text_shown,
            base_sp=15,
            min_height_dp=56,
        )
        btn.bind(on_release=lambda _b, txt=text_shown: self._use_quick_phrase(txt))
        self.phrases_box.add_widget(btn)

    def _use_quick_phrase(self, text: str) -> None:
        self.input_field.text = text
        self._run_translation()

    def _run_translation(self) -> None:
        src = "es" if self._es_to_indigenous else self._selected_lang
        tgt = self._selected_lang if self._es_to_indigenous else "es"
        res = self.app_ref.container.translator.translate(self.input_field.text, src, tgt)
        self._last_result = res

        engine_labels = {
            "offline_memory": "Diccionario guardado en tu teléfono (Exacto)",
            "offline_fuzzy": "Coincidencia cercana sin internet",
            "cloud_nmt": "Traducción mejorada en línea",
        }
        self.result_engine_lbl.text = engine_labels.get(res.engine_used, res.engine_used)
        self.result_text_lbl.text = res.translated_text or "Sin resultado"
        self.result_phonetic_lbl.text = (
            f"Pronunciación aproximada: {res.phonetic_guide}"
            if res.phonetic_guide
            else "Español ciudadano simplificado"
        )
        self.result_note_lbl.text = res.citizen_note

    def _speak_translation(self) -> None:
        if self._last_result is None:
            return
        if self._last_result.audio_clip and self.app_ref.container.audio_voice.play_audio_file(
            self._last_result.audio_clip
        ):
            return
        spoken = self._last_result.phonetic_guide or self._last_result.translated_text
        self.app_ref.container.audio_voice.speak(spoken)

    def _start_voice_input(self) -> None:
        lang = "es-MX"  # Base acústica en Android RecognizerIntent
        self.result_note_lbl.text = "Escuchando micrófono..."
        self.app_ref.container.audio_voice.listen_once(
            lang_code=lang,
            on_result=lambda txt: Clock.schedule_once(lambda _dt: self._on_stt_ok(txt), 0),
            on_error=lambda err: Clock.schedule_once(lambda _dt: self._on_stt_err(err), 0),
        )

    def _on_stt_ok(self, text: str) -> None:
        self.input_field.text = text
        self._run_translation()

    def _on_stt_err(self, err: str) -> None:
        self.result_note_lbl.text = err
