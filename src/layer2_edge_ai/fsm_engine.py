"""Motor de Máquina de Estados Finitos (FSM) declarativa para trámites guiados."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from src.domain.interfaces import EncryptedRepositoryPort
from src.domain.models import FSMState, FSMTransition, ProcedureProgress, WorkflowFSM


class FSMTransitionError(ValueError):
    """Error de negocio amigable cuando falta una precondición para avanzar."""


class WorkflowFSMEngine:
    """Evalúa precondiciones, avanza/retrocede pasos y persiste el progreso local."""

    def __init__(self, repository: EncryptedRepositoryPort | None = None) -> None:
        self._repository = repository

    @staticmethod
    def from_dict(data: dict[str, Any]) -> WorkflowFSM:
        """Construye una WorkflowFSM validada desde el esquema workflow.json."""
        states: dict[str, FSMState] = {}
        for raw_state in data.get("states", []):
            next_raw = raw_state.get("next_transition")
            next_transition = (
                FSMTransition(
                    target_state=next_raw["target_state"],
                    condition=next_raw.get("condition", "always"),
                    label=next_raw.get("label", "Siguiente paso"),
                )
                if next_raw
                else None
            )
            state_obj = FSMState(
                state_id=raw_state["state_id"],
                step_number=int(raw_state["step_number"]),
                title=raw_state["title"],
                citizen_instruction=raw_state["citizen_instruction"],
                pictogram_id=raw_state.get("pictogram_id", "documents"),
                checklist_items=tuple(raw_state.get("checklist_items", [])),
                translations=dict(raw_state.get("translations", {})),
                audio_script_es=raw_state.get("audio_script_es", ""),
                audio_clips=dict(raw_state.get("audio_clips", {})),
                office_options=tuple(raw_state.get("office_options", [])),
                next_transition=next_transition,
                prev_state=raw_state.get("prev_state"),
                is_terminal=bool(raw_state.get("is_terminal", False)),
            )
            states[state_obj.state_id] = state_obj

        initial_state = data["initial_state"]
        if initial_state not in states:
            raise ValueError(f"Estado inicial inválido: {initial_state}")

        return WorkflowFSM(
            pack_id=data["pack_id"],
            title=data["title"],
            category=data.get("category", "General"),
            version=data.get("version", "1.0.0"),
            estimated_time=data.get("estimated_time", "1 a 2 horas"),
            cost_summary=data.get("cost_summary", "Consultar tarifa o exención"),
            initial_state=initial_state,
            states=states,
        )

    def load_or_initialize_progress(self, workflow: WorkflowFSM) -> ProcedureProgress:
        """Recupera el último estado guardado para reanudar exactamente donde se quedó."""
        if self._repository is not None:
            saved = self._repository.load_progress(workflow.pack_id)
            if saved is not None and saved.current_state_id in workflow.states:
                return saved

        progress = ProcedureProgress(
            pack_id=workflow.pack_id,
            current_state_id=workflow.initial_state,
            completed_checklist={},
            selected_office="",
            payment_exempt=False,
            updated_at_iso=_utc_now_iso(),
        )
        self._persist(progress)
        return progress

    def get_current_state(
        self, workflow: WorkflowFSM, progress: ProcedureProgress
    ) -> FSMState:
        """Devuelve el nodo activo de la máquina de estados."""
        return workflow.states[progress.current_state_id]

    def get_progress_ratio(
        self, workflow: WorkflowFSM, progress: ProcedureProgress
    ) -> float:
        """Proporción de avance (0.0 a 1.0) para la barra visual superior."""
        total = max(1, len(workflow.states))
        current = self.get_current_state(workflow, progress)
        if current.is_terminal:
            return 1.0
        return round(current.step_number / float(total), 2)

    def toggle_checklist_item(
        self, workflow: WorkflowFSM, progress: ProcedureProgress, item: str
    ) -> ProcedureProgress:
        """Marca o desmarca un requisito del paso actual y persiste al instante."""
        state_id = progress.current_state_id
        current_items = progress.completed_checklist.setdefault(state_id, [])
        if item in current_items:
            current_items.remove(item)
        else:
            current_items.append(item)
        progress.updated_at_iso = _utc_now_iso()
        self._persist(progress)
        return progress

    def select_office(
        self, progress: ProcedureProgress, office_name: str
    ) -> ProcedureProgress:
        """Registra la ventanilla o sede elegida por el ciudadano."""
        progress.selected_office = office_name.strip()
        progress.updated_at_iso = _utc_now_iso()
        self._persist(progress)
        return progress

    def set_payment_exempt(
        self, progress: ProcedureProgress, exempt: bool
    ) -> ProcedureProgress:
        """Registra si el trámite aplica exención de tarifa o comprobante validado."""
        progress.payment_exempt = exempt
        progress.updated_at_iso = _utc_now_iso()
        self._persist(progress)
        return progress

    def can_advance(
        self, workflow: WorkflowFSM, progress: ProcedureProgress
    ) -> tuple[bool, str]:
        """Verifica las precondiciones locales del estado actual antes de transicionar."""
        state = self.get_current_state(workflow, progress)
        if state.is_terminal or state.next_transition is None:
            return False, "Este trámite ya concluyó."

        cond = state.next_transition.condition
        if cond == "always":
            return True, ""

        if cond == "checklist_complete":
            checked = set(progress.completed_checklist.get(state.state_id, []))
            missing = [item for item in state.checklist_items if item not in checked]
            if missing:
                return (
                    False,
                    f"Marca primero los requisitos pendientes ({len(missing)} por confirmar).",
                )
            return True, ""

        if cond == "office_selected":
            if state.office_options and not progress.selected_office:
                return False, "Elige primero la oficina o ventanilla a la que vas a ir."
            return True, ""

        if cond == "payment_or_exempt":
            checked = set(progress.completed_checklist.get(state.state_id, []))
            if progress.payment_exempt or (
                state.checklist_items and all(i in checked for i in state.checklist_items)
            ):
                return True, ""
            return (
                False,
                "Confirma tu comprobante de pago o selecciona si aplicas a trámite gratuito.",
            )

        return True, ""

    def advance(
        self, workflow: WorkflowFSM, progress: ProcedureProgress
    ) -> ProcedureProgress:
        """Ejecuta transición al siguiente estado si las precondiciones se cumplen."""
        ok, reason = self.can_advance(workflow, progress)
        if not ok:
            raise FSMTransitionError(reason)

        state = self.get_current_state(workflow, progress)
        assert state.next_transition is not None
        target = state.next_transition.target_state
        if target not in workflow.states:
            raise FSMTransitionError(f"Estado destino inexistente: {target}")

        progress.current_state_id = target
        progress.updated_at_iso = _utc_now_iso()
        self._persist(progress)
        return progress

    def go_back(
        self, workflow: WorkflowFSM, progress: ProcedureProgress
    ) -> ProcedureProgress:
        """Permite retroceder al paso anterior sin perder marcas ya realizadas."""
        state = self.get_current_state(workflow, progress)
        if not state.prev_state or state.prev_state not in workflow.states:
            return progress
        progress.current_state_id = state.prev_state
        progress.updated_at_iso = _utc_now_iso()
        self._persist(progress)
        return progress

    def reset_progress(self, workflow: WorkflowFSM) -> ProcedureProgress:
        """Reinicia un trámite al estado inicial S01."""
        progress = ProcedureProgress(
            pack_id=workflow.pack_id,
            current_state_id=workflow.initial_state,
            completed_checklist={},
            selected_office="",
            payment_exempt=False,
            updated_at_iso=_utc_now_iso(),
        )
        self._persist(progress)
        return progress

    def _persist(self, progress: ProcedureProgress) -> None:
        if self._repository is not None:
            self._repository.save_progress(progress)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
