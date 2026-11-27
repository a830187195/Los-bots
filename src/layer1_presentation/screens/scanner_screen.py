"""Módulo 2: Intérprete de Documentos Oficiales con OCR local y Privacy by Design."""

from __future__ import annotations

import threading
from pathlib import Path
from typing import TYPE_CHECKING

from kivy.clock import Clock  # type: ignore import-not-found
from kivy.metrics import dp  # type: ignore import-not-found
from kivy.uix.boxlayout import BoxLayout  # type: ignore import-not-found
from kivy.uix.textinput import TextInput  # type: ignore import-not-found

from src.domain.models import DocumentAnalysisResult
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

_SAMPLE_DOCS: dict[str, tuple[str, str]] = {
    "Acta de Nacimiento": (
        "ESTADOS UNIDOS MEXICANOS. REGISTRO CIVIL. ACTA DE NACIMIENTO. "
        "OFICIALIA 001. LUGAR DE NACIMIENTO: PUEBLA. FOLIO: ACTA-9928412. "
        "Deberá presentar en original y copia fotostática legible para cotejo documental.",
        "document_acta",
    ),
    "Citatorio con Jerga": (
        "CITATORIO OFICIAL. OFICIO: DGA-448120. "
        "Se requiere comparecer de manera personal en un término perentorio de 5 días hábiles "
        "para acreditar personalidad jurídica mediante instrumento público o identificación oficial vigente "
        "y enterar el pago de derechos por $185.00 MXN antes del 15/12/2026.",
        "document_official",
    ),
    "Constancia CURP": (
        "SECRETARIA DE GOBERNACION. RENAPO. CLAVE UNICA DE REGISTRO DE POBLACION. "
        "CONSTANCIA CURP. CURP: ABCD900101HPLRRS09. NOMBRE: MARIA LOPEZ. "
        "Trámite gratuito, conservar copia legible.",
        "document_curp",
    ),
    "Documento IMSS": (
        "INSTITUTO MEXICANO DEL SEGURO SOCIAL. CONSTANCIA DE VIGENCIA DE DERECHOS. "
        "NSS: 12345678901. UNIDAD DE MEDICINA FAMILIAR UMF 6. "
        "Acudir con identificación oficial vigente.",
        "document_imss",
    ),
}


class ScannerScreen(BaseAccessibleScreen):
    """Escanea documentos en RAM local sin enviar ni guardar fotos o PII."""

    def __init__(self, app_ref: MiTramiteJustoApp, **kwargs: object) -> None:
        super().__init__(
            app_ref=app_ref,
            screen_title="Intérprete de Documentos",
            show_back=True,
            name="scanner",
            **kwargs,
        )
        self._last_analysis: DocumentAnalysisResult | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        # Banner de privacidad en memoria volátil
        priv_card = AccessibleCard(
            theme=self.theme,
            bg_rgba=self.theme.success_bg,
            border_rgba=self.theme.success_fg,
        )
        priv_card.add_widget(
            AccessibleLabel(
                theme=self.theme,
                base_sp=15,
                bold=True,
                color_rgba=self.theme.success_fg,
                text="Privacidad protegida: tus fotos y datos (CURP, nombres) se analizan solo en la memoria temporal de tu teléfono y nunca se suben a internet.",
            )
        )
        self.content_box.add_widget(priv_card)

        # Controles de cámara y galería
        cam_card = AccessibleCard(theme=self.theme)
        cam_card.add_widget(
            AccessibleLabel(
                theme=self.theme,
                base_sp=18,
                bold=True,
                text="1. Toma foto o elige un documento:",
            )
        )
        btn_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(62), spacing=dp(12))
        btn_cam = AccessibleButton(
            theme=self.theme,
            bg_rgba=self.theme.primary_blue,
            fg_rgba=self.theme.text_on_dark,
            text="Tomar Foto",
            min_height_dp=56,
        )
        btn_cam.bind(on_release=lambda *_a: self._capture_camera())

        btn_gal = AccessibleButton(
            theme=self.theme,
            bg_rgba=self.theme.brand_olive,
            fg_rgba=self.theme.text_on_dark,
            text="Abrir Galería",
            min_height_dp=56,
        )
        btn_gal.bind(on_release=lambda *_a: self._pick_gallery())
        btn_row.add_widget(btn_cam)
        btn_row.add_widget(btn_gal)
        cam_card.add_widget(btn_row)

        cam_card.add_widget(
            AccessibleLabel(
                theme=self.theme,
                base_sp=15,
                bold=True,
                color_rgba=self.theme.text_secondary,
                text="O prueba al instante con un documento de ejemplo:",
            )
        )
        for sample_name in _SAMPLE_DOCS:
            sample_btn = AccessibleButton(
                theme=self.theme,
                bg_rgba=self.theme.surface_tinted,
                fg_rgba=self.theme.primary_blue,
                border_rgba=self.theme.primary_blue,
                text=f"Ejemplo: {sample_name}",
                base_sp=15,
                min_height_dp=56,
            )
            sample_btn.bind(on_release=lambda _b, sn=sample_name: self._run_sample(sn))
            cam_card.add_widget(sample_btn)

        # Opción manual para pegar texto legal difícil
        self.manual_input = TextInput(
            hint_text="También puedes escribir o pegar aquí una frase difícil de un citatorio...",
            multiline=True,
            size_hint_y=None,
            height=dp(84),
            font_size=self.theme.sp_size(16),
            background_color=(1, 1, 1, 1),
            foreground_color=self.theme.text_primary,
            padding=(dp(10), dp(10)),
        )
        cam_card.add_widget(self.manual_input)
        btn_text = AccessibleButton(
            theme=self.theme,
            bg_rgba=self.theme.primary_blue,
            fg_rgba=self.theme.text_on_dark,
            text="Explicar texto en palabras sencillas",
            base_sp=15,
            min_height_dp=56,
        )
        btn_text.bind(on_release=lambda *_a: self._analyze_raw_text(self.manual_input.text))
        cam_card.add_widget(btn_text)
        self.content_box.add_widget(cam_card)

        # Tarjeta de resultado ciudadano
        self.result_card = AccessibleCard(
            theme=self.theme,
            bg_rgba=self.theme.surface_card,
            border_rgba=self.theme.primary_blue,
        )
        top_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(88), spacing=dp(12))
        self.res_pictogram = PictogramWidget(theme=self.theme, pictogram_id="document_acta", size_dp=80)
        top_row.add_widget(self.res_pictogram)

        title_col = BoxLayout(orientation="vertical", spacing=dp(4))
        self.res_title = AccessibleLabel(
            theme=self.theme,
            base_sp=20,
            bold=True,
            color_rgba=self.theme.primary_blue,
            text="Identificado: Acta de Nacimiento",
        )
        self.res_badge = AccessibleLabel(
            theme=self.theme,
            base_sp=14,
            bold=True,
            color_rgba=self.theme.warning_fg,
            text="ACCIÓN: CONSERVAR ORIGINAL Y ENTREGAR COPIA",
        )
        title_col.add_widget(self.res_title)
        title_col.add_widget(self.res_badge)
        top_row.add_widget(title_col)
        self.result_card.add_widget(top_row)

        self.res_purpose = AccessibleLabel(
            theme=self.theme,
            base_sp=17,
            text="",
        )
        self.res_action = AccessibleLabel(
            theme=self.theme,
            base_sp=16,
            color_rgba=self.theme.text_secondary,
            text="",
        )
        self.res_clauses = AccessibleLabel(
            theme=self.theme,
            base_sp=15,
            color_rgba=self.theme.brand_olive,
            text="",
        )
        self.result_card.add_widget(self.res_purpose)
        self.result_card.add_widget(self.res_action)
        self.result_card.add_widget(self.res_clauses)

        self.result_card.add_widget(
            SpeakerButton(
                theme=self.theme,
                label_text="Escuchar explicación clara",
                on_speak=self._speak_analysis,
            )
        )
        self.start_guide_btn = AccessibleButton(
            theme=self.theme,
            bg_rgba=self.theme.primary_blue,
            fg_rgba=self.theme.text_on_dark,
            text="Iniciar Guía Paso a Paso de este trámite",
            min_height_dp=56,
        )
        self.start_guide_btn.bind(on_release=lambda *_a: self._open_recommended_guide())
        self.result_card.add_widget(self.start_guide_btn)

        self.content_box.add_widget(self.result_card)
        self._run_sample("Acta de Nacimiento")

    def _capture_camera(self) -> None:
        self.res_title.text = "Abriendo cámara..."
        self.app_ref.container.camera_bridge.capture_from_camera(
            lambda path: Clock.schedule_once(lambda _dt: self._on_image_selected(path), 0)
        )

    def _pick_gallery(self) -> None:
        self.res_title.text = "Seleccionando imagen..."
        self.app_ref.container.camera_bridge.pick_from_gallery(
            lambda path: Clock.schedule_once(lambda _dt: self._on_image_selected(path), 0)
        )

    def _on_image_selected(self, path_str: str | None) -> None:
        if not path_str:
            self.res_title.text = "No se eligió imagen (puedes probar los ejemplos)"
            return

        self.res_title.text = "Analizando en memoria local..."

        def _worker() -> None:
            path = Path(path_str)
            boxes = self.app_ref.container.ocr_engine.analyze_image_file(
                path,
                hint_text=None,
            )
            if not boxes:
                # Si la foto real no tuvo motor Tesseract/MLKit en desktop, indicarlo claro
                analysis = self.app_ref.container.doc_interpreter.analyze_text("")
            else:
                analysis = self.app_ref.container.doc_interpreter.analyze_ocr_boxes(boxes)
            Clock.schedule_once(lambda _dt: self._render_analysis(analysis), 0)

        threading.Thread(target=_worker, daemon=True).start()

    def _run_sample(self, sample_name: str) -> None:
        sample_text, _ = _SAMPLE_DOCS[sample_name]
        boxes = self.app_ref.container.ocr_engine.extract_text_boxes(
            b"", hint_text=sample_text
        )
        analysis = self.app_ref.container.doc_interpreter.analyze_ocr_boxes(boxes)
        self._render_analysis(analysis)

    def _analyze_raw_text(self, raw_text: str) -> None:
        if not raw_text.strip():
            return
        analysis = self.app_ref.container.doc_interpreter.analyze_text(raw_text)
        self._render_analysis(analysis)

    def _render_analysis(self, res: DocumentAnalysisResult) -> None:
        self._last_analysis = res
        self.res_pictogram.set_pictogram(res.pictogram_id)
        self.res_title.text = f"Identificado: {res.document_title}"
        self.res_badge.text = f"ACCIÓN REQUERIDA: {res.action_badge}"
        self.res_purpose.text = f"Para qué sirve: {res.purpose_citizen}"

        extra_parts: list[str] = [f"Qué debes hacer: {res.action_details}"]
        if res.detected_folios_masked:
            extra_parts.append(f"Folio protegido: {', '.join(res.detected_folios_masked)}")
        if res.detected_dates:
            extra_parts.append(f"Fechas detectadas: {', '.join(res.detected_dates)}")
        if res.detected_amounts:
            extra_parts.append(f"Montos detectados: {', '.join(res.detected_amounts)}")
        self.res_action.text = "\n".join(extra_parts)

        if res.simplified_clauses:
            lines = ["Frases legales traducidas a lenguaje ciudadano:"]
            for formal, simple in res.simplified_clauses:
                lines.append(f"• Dice: \"{formal}\" -> Significa: {simple}")
            self.res_clauses.text = "\n".join(lines)
        else:
            self.res_clauses.text = "Listo en memoria local sin guardar datos personales."

        self.start_guide_btn.disabled = not bool(res.recommended_pack_id)

    def _speak_analysis(self) -> None:
        if self._last_analysis is None:
            return
        res = self._last_analysis
        script = (
            f"Documento identificado: {res.document_title}. "
            f"Para qué sirve: {res.purpose_citizen} "
            f"Acción requerida: {res.action_badge}. {res.action_details}"
        )
        if res.simplified_clauses:
            script += " Explicación sencilla: " + res.simplified_clauses[0][1]
        self.app_ref.container.audio_voice.speak(script)

    def _open_recommended_guide(self) -> None:
        if self._last_analysis and self._last_analysis.recommended_pack_id:
            self.app_ref.open_guide_pack(self._last_analysis.recommended_pack_id)
