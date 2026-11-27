"""Módulo 4: Guía Interactiva Paso a Paso con Máquina de Estados (FSM), Audio y Pictogramas."""

from __future__ import annotations

from typing import TYPE_CHECKING

from kivy.metrics import dp  # type: ignore import-not-found
from kivy.uix.boxlayout import BoxLayout  # type: ignore import-not-found

from src.domain.models import ProcedureProgress, WorkflowFSM
from src.layer1_presentation.screens.base_screen import BaseAccessibleScreen
from src.layer1_presentation.widgets.accessible import (
    AccessibleButton,
    AccessibleCard,
    AccessibleLabel,
    SpeakerButton,
    StepProgressBar,
)
from src.layer1_presentation.widgets.pictograms import PictogramWidget
from src.layer2_edge_ai.fsm_engine import FSMTransitionError

if TYPE_CHECKING:
    from src.layer1_presentation.app import MiTramiteJustoApp


class GuideScreen(BaseAccessibleScreen):
    """Guía interactiva paso a paso sincronizada (FSM + Pictograma + Audio + Persistencia)."""

    def __init__(self, app_ref: MiTramiteJustoApp, **kwargs: object) -> None:
        super().__init__(
            app_ref=app_ref,
            screen_title="Guía Paso a Paso",
            show_back=True,
            name="guide",
            **kwargs,
        )
        self._active_pack_id = "acta_nacimiento"
        self._workflow: WorkflowFSM | None = None
        self._progress: ProcedureProgress | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        # Selector rápido de trámite
        selector_card = AccessibleCard(theme=self.theme)
        selector_card.add_widget(
            AccessibleLabel(
                theme=self.theme,
                base_sp=16,
                bold=True,
                text="Elige el trámite que vas a realizar:",
            )
        )
        self._pack_buttons_box = BoxLayout(
            orientation="vertical", size_hint_y=None, spacing=dp(8)
        )
        self._pack_buttons_box.bind(minimum_height=self._pack_buttons_box.setter("height"))
        self._pack_btn_map: dict[str, AccessibleButton] = {}
        for item in self.app_ref.container.package_manager.list_available_catalog():
            pid = str(item["pack_id"])
            btn = AccessibleButton(
                theme=self.theme,
                text=str(item["title"]),
                base_sp=15,
                min_height_dp=56,
            )
            btn.bind(on_release=lambda _b, p=pid: self.load_pack(p))
            self._pack_btn_map[pid] = btn
            self._pack_buttons_box.add_widget(btn)
        selector_card.add_widget(self._pack_buttons_box)
        self.content_box.add_widget(selector_card)

        # Barra de progreso superior
        self.progress_bar = StepProgressBar(self.theme)
        self.content_box.add_widget(self.progress_bar)

        # Tarjeta principal del estado FSM sincronizada (Pictograma + Texto + Lengua + Audio)
        self.step_card = AccessibleCard(
            theme=self.theme,
            bg_rgba=self.theme.surface_card,
            border_rgba=self.theme.primary_blue,
        )
        header_row = BoxLayout(
            orientation="horizontal", size_hint_y=None, height=dp(92), spacing=dp(12)
        )
        self.step_pictogram = PictogramWidget(theme=self.theme, pictogram_id="documents", size_dp=84)
        header_row.add_widget(self.step_pictogram)

        title_col = BoxLayout(orientation="vertical", spacing=dp(4))
        self.step_state_badge = AccessibleLabel(
            theme=self.theme,
            base_sp=13,
            bold=True,
            color_rgba=self.theme.brand_olive,
            text="ESTADO: S01",
        )
        self.step_title_lbl = AccessibleLabel(
            theme=self.theme,
            base_sp=21,
            bold=True,
            color_rgba=self.theme.primary_blue,
            text="Reunir Papeles",
        )
        title_col.add_widget(self.step_state_badge)
        title_col.add_widget(self.step_title_lbl)
        header_row.add_widget(title_col)
        self.step_card.add_widget(header_row)

        self.step_instruction_lbl = AccessibleLabel(
            theme=self.theme,
            base_sp=18,
            text="",
        )
        self.step_card.add_widget(self.step_instruction_lbl)

        # Traducción automática al idioma originario preferido
        self.indigenous_box = AccessibleCard(
            theme=self.theme,
            bg_rgba=self.theme.surface_tinted,
            border_rgba=self.theme.brand_olive,
        )
        self.indigenous_lbl = AccessibleLabel(
            theme=self.theme,
            base_sp=15,
            bold=True,
            color_rgba=self.theme.brand_olive,
            text="",
        )
        self.indigenous_box.add_widget(self.indigenous_lbl)
        self.step_card.add_widget(self.indigenous_box)

        # Lista interactiva (checklist / sedes / exención)
        self.interactive_box = BoxLayout(
            orientation="vertical", size_hint_y=None, spacing=dp(10)
        )
        self.interactive_box.bind(minimum_height=self.interactive_box.setter("height"))
        self.step_card.add_widget(self.interactive_box)

        # Botón de voz con resaltado visual
        self.step_card.add_widget(
            SpeakerButton(
                theme=self.theme,
                label_text="Escuchar instrucciones de este paso",
                on_speak=self._speak_current_step,
            )
        )

        self.validation_msg = AccessibleLabel(
            theme=self.theme,
            base_sp=15,
            bold=True,
            color_rgba=self.theme.warning_fg,
            text="",
        )
        self.step_card.add_widget(self.validation_msg)

        # Botones de navegación FSM (Anterior / Siguiente)
        nav_row = BoxLayout(
            orientation="horizontal", size_hint_y=None, height=dp(64), spacing=dp(12)
        )
        self.prev_btn = AccessibleButton(
            theme=self.theme,
            bg_rgba=self.theme.surface_tinted,
            fg_rgba=self.theme.primary_blue,
            border_rgba=self.theme.primary_blue,
            text="< Paso Anterior",
            base_sp=16,
            min_height_dp=56,
            size_hint_x=0.45,
        )
        self.prev_btn.bind(on_release=lambda *_a: self._go_prev())

        self.next_btn = AccessibleButton(
            theme=self.theme,
            bg_rgba=self.theme.primary_blue,
            fg_rgba=self.theme.text_on_dark,
            text="Siguiente Paso >",
            base_sp=16,
            min_height_dp=56,
        )
        self.next_btn.bind(on_release=lambda *_a: self._go_next())

        nav_row.add_widget(self.prev_btn)
        nav_row.add_widget(self.next_btn)
        self.step_card.add_widget(nav_row)

        reset_btn = AccessibleButton(
            theme=self.theme,
            bg_rgba=self.theme.surface_card,
            fg_rgba=self.theme.text_secondary,
            border_rgba=self.theme.border_subtle,
            text="Reiniciar este trámite desde el paso 1",
            base_sp=14,
            min_height_dp=56,
        )
        reset_btn.bind(on_release=lambda *_a: self._reset_workflow())
        self.step_card.add_widget(reset_btn)

        self.content_box.add_widget(self.step_card)
        self.load_pack(self._active_pack_id)

    def on_pre_enter(self, *_args: object) -> None:
        super().on_pre_enter(*_args)
        self._render_state()

    def load_pack(self, pack_id: str) -> None:
        """Carga el trámite solicitado y reanuda exactamente en el último estado guardado."""
        self._active_pack_id = pack_id
        c = self.app_ref.container
        self._workflow = c.package_manager.load_workflow(pack_id)
        self._progress = c.fsm_engine.load_or_initialize_progress(self._workflow)
        self.validation_msg.text = ""
        self._render_state()

    def _render_state(self) -> None:
        if self._workflow is None or self._progress is None:
            return
        c = self.app_ref.container

        for pid, btn in self._pack_btn_map.items():
            if pid == self._active_pack_id:
                btn.set_colors(self.theme.primary_blue, self.theme.text_on_dark)
            else:
                btn.set_colors(
                    self.theme.surface_tinted,
                    self.theme.primary_blue,
                    self.theme.primary_blue,
                )

        state = c.fsm_engine.get_current_state(self._workflow, self._progress)
        ratio = c.fsm_engine.get_progress_ratio(self._workflow, self._progress)
        self.progress_bar.set_progress(
            state.step_number, len(self._workflow.states), ratio
        )

        self.step_pictogram.set_pictogram(state.pictogram_id)
        self.step_state_badge.text = (
            f"Paso {state.step_number} de {len(self._workflow.states)} · {self._workflow.cost_summary}"
        )
        self.step_title_lbl.text = f"Paso {state.step_number}: {state.title}"
        self.step_instruction_lbl.text = state.citizen_instruction

        pref_lang = c.config.preferred_language
        native_txt = state.translations.get(pref_lang, "")
        if native_txt:
            pack = c.lang_registry.get_pack(pref_lang)
            lname = pack.display_name.split("(")[0].strip() if pack else pref_lang
            self.indigenous_lbl.text = f"En {lname}: {native_txt}"
        else:
            self.indigenous_lbl.text = "Disponible en Español ciudadano claro."

        if state.is_terminal:
            self.step_card.set_card_colors(self.theme.success_bg, self.theme.success_fg)
        else:
            self.step_card.set_card_colors(self.theme.surface_card, self.theme.primary_blue)

        # Controles interactivos según nodo FSM
        self.interactive_box.clear_widgets()
        checked_set = set(self._progress.completed_checklist.get(state.state_id, []))
        for item in state.checklist_items:
            is_checked = item in checked_set
            prefix = "[LISTO] " if is_checked else "[TOCAR] "
            chk_btn = AccessibleButton(
                theme=self.theme,
                bg_rgba=self.theme.success_bg if is_checked else self.theme.surface_tinted,
                fg_rgba=self.theme.success_fg if is_checked else self.theme.text_primary,
                border_rgba=self.theme.success_fg if is_checked else self.theme.border_subtle,
                text=prefix + item,
                base_sp=15,
                min_height_dp=56,
            )
            chk_btn.bind(on_release=lambda _b, it=item: self._toggle_item(it))
            self.interactive_box.add_widget(chk_btn)

        for office in state.office_options:
            selected = self._progress.selected_office == office
            prefix = "[SEDE ELEGIDA] " if selected else "[ELEGIR SEDE] "
            off_btn = AccessibleButton(
                theme=self.theme,
                bg_rgba=self.theme.primary_blue if selected else self.theme.surface_tinted,
                fg_rgba=self.theme.text_on_dark if selected else self.theme.primary_blue,
                border_rgba=self.theme.primary_blue,
                text=prefix + office,
                base_sp=15,
                min_height_dp=56,
            )
            off_btn.bind(on_release=lambda _b, of=office: self._select_office(of))
            self.interactive_box.add_widget(off_btn)

        if state.next_transition and state.next_transition.condition == "payment_or_exempt":
            ex = self._progress.payment_exempt
            ex_btn = AccessibleButton(
                theme=self.theme,
                bg_rgba=self.theme.success_bg if ex else self.theme.warning_bg,
                fg_rgba=self.theme.success_fg if ex else self.theme.warning_fg,
                border_rgba=self.theme.brand_olive,
                text=(
                    "[CONFIRMADO] Trámite gratuito / Exención aplicada"
                    if ex
                    else "Aplicar Exención o Confirmar Trámite Gratuito"
                ),
                base_sp=15,
                min_height_dp=56,
            )
            ex_btn.bind(on_release=lambda *_a: self._toggle_exempt())
            self.interactive_box.add_widget(ex_btn)

        self.prev_btn.disabled = state.prev_state is None
        if state.next_transition:
            self.next_btn.disabled = False
            self.next_btn.text = f"{state.next_transition.label} >"
        else:
            self.next_btn.disabled = True
            self.next_btn.text = "Trámite Finalizado"

    def _toggle_item(self, item: str) -> None:
        if self._workflow is None or self._progress is None:
            return
        self._progress = self.app_ref.container.fsm_engine.toggle_checklist_item(
            self._workflow, self._progress, item
        )
        self.validation_msg.text = ""
        self._render_state()

    def _select_office(self, office: str) -> None:
        if self._progress is None:
            return
        self._progress = self.app_ref.container.fsm_engine.select_office(
            self._progress, office
        )
        self.validation_msg.text = ""
        self._render_state()

    def _toggle_exempt(self) -> None:
        if self._progress is None:
            return
        self._progress = self.app_ref.container.fsm_engine.set_payment_exempt(
            self._progress, not self._progress.payment_exempt
        )
        self.validation_msg.text = ""
        self._render_state()

    def _go_next(self) -> None:
        if self._workflow is None or self._progress is None:
            return
        try:
            self._progress = self.app_ref.container.fsm_engine.advance(
                self._workflow, self._progress
            )
            self.validation_msg.text = ""
            self._render_state()
        except FSMTransitionError as exc:
            self.validation_msg.text = str(exc)
            self.app_ref.container.audio_voice.speak(str(exc))

    def _go_prev(self) -> None:
        if self._workflow is None or self._progress is None:
            return
        self._progress = self.app_ref.container.fsm_engine.go_back(
            self._workflow, self._progress
        )
        self.validation_msg.text = ""
        self._render_state()

    def _reset_workflow(self) -> None:
        if self._workflow is None:
            return
        self._progress = self.app_ref.container.fsm_engine.reset_progress(self._workflow)
        self.validation_msg.text = "Trámite reiniciado desde el paso 1."
        self._render_state()

    def _speak_current_step(self) -> None:
        if self._workflow is None or self._progress is None:
            return
        state = self.app_ref.container.fsm_engine.get_current_state(
            self._workflow, self._progress
        )
        self.step_card.set_card_colors(self.theme.warning_bg, self.theme.brand_olive)
        script = state.audio_script_es or f"{state.title}. {state.citizen_instruction}"
        self.app_ref.container.audio_voice.speak(script)
