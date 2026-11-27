"""Módulo 3: Gestor de Paquetes .mtjpack, Modo Sin Conexión y Sincronización Delta."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from kivy.metrics import dp  # type: ignore import-not-found
from kivy.uix.boxlayout import BoxLayout  # type: ignore import-not-found

from src.layer1_presentation.screens.base_screen import BaseAccessibleScreen
from src.layer1_presentation.widgets.accessible import (
    AccessibleButton,
    AccessibleCard,
    AccessibleLabel,
    SpeakerButton,
)

if TYPE_CHECKING:
    from src.layer1_presentation.app import MiTramiteJustoApp


class OfflineHubScreen(BaseAccessibleScreen):
    """Administra paquetes descargables .mtjpack, deltas SHA-256 y modo avión."""

    def __init__(self, app_ref: MiTramiteJustoApp, **kwargs: object) -> None:
        super().__init__(
            app_ref=app_ref,
            screen_title="Modo Sin Conexión",
            show_back=True,
            name="offline_hub",
            **kwargs,
        )
        self._build_ui()

    def _build_ui(self) -> None:
        # Panel de estado Offline-First y seguridad en reposo
        status_card = AccessibleCard(
            theme=self.theme,
            bg_rgba=self.theme.surface_tinted,
            border_rgba=self.theme.primary_blue,
        )
        status_card.add_widget(
            AccessibleLabel(
                theme=self.theme,
                base_sp=18,
                bold=True,
                color_rgba=self.theme.primary_blue,
                text="Tus trámites siempre disponibles sin internet",
            )
        )
        self.security_lbl = AccessibleLabel(
            theme=self.theme,
            base_sp=14,
            color_rgba=self.theme.text_secondary,
            text="",
        )
        status_card.add_widget(self.security_lbl)

        self.offline_toggle_btn = AccessibleButton(
            theme=self.theme,
            bg_rgba=self.theme.brand_olive,
            fg_rgba=self.theme.text_on_dark,
            text="Simular Modo Avión (Sin Conexión)",
            base_sp=15,
            min_height_dp=56,
        )
        self.offline_toggle_btn.bind(on_release=lambda *_a: self._toggle_offline_mode())
        status_card.add_widget(self.offline_toggle_btn)

        sync_btn = AccessibleButton(
            theme=self.theme,
            bg_rgba=self.theme.primary_blue,
            fg_rgba=self.theme.text_on_dark,
            text="Buscar actualizaciones de guías",
            base_sp=15,
            min_height_dp=56,
        )
        sync_btn.bind(on_release=lambda *_a: self._run_sync_check())
        status_card.add_widget(sync_btn)
        status_card.add_widget(
            SpeakerButton(
                theme=self.theme,
                label_text="Escuchar estado sin conexión",
                on_speak=self._speak_offline_status,
            )
        )
        self.content_box.add_widget(status_card)

        self.feedback_lbl = AccessibleLabel(
            theme=self.theme,
            base_sp=15,
            bold=True,
            color_rgba=self.theme.brand_olive,
            text="",
        )
        self.content_box.add_widget(self.feedback_lbl)

        # Lista de paquetes de trámites (.mtjpack)
        self.packs_container = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(14))
        self.packs_container.bind(minimum_height=self.packs_container.setter("height"))
        self.content_box.add_widget(self.packs_container)

    def on_pre_enter(self, *_args: object) -> None:
        super().on_pre_enter(*_args)
        self._refresh_catalog()

    def _refresh_catalog(self) -> None:
        c = self.app_ref.container
        pending = c.sync_queue.pending_count()
        self.security_lbl.text = (
            "Tu información está protegida con llave segura en este dispositivo.\n"
            f"Actualizaciones pendientes por revisar: {pending}"
        )
        is_forced = c.connectivity.force_offline
        self.offline_toggle_btn.text = (
            "Modo Avión de prueba: ACTIVADO (toca para desactivar)"
            if is_forced
            else "Probar sin internet (Simular Modo Avión)"
        )

        self.packs_container.clear_widgets()
        for item in c.package_manager.list_available_catalog():
            self._add_pack_card(item)

    def _add_pack_card(self, item: dict[str, Any]) -> None:
        installed = bool(item["installed"])
        card = AccessibleCard(
            theme=self.theme,
            bg_rgba=self.theme.surface_card,
            border_rgba=self.theme.success_fg if installed else self.theme.border_subtle,
        )
        badge = "LISTA PARA USAR SIN INTERNET" if installed else "DISPONIBLE PARA GUARDAR"
        card.add_widget(
            AccessibleLabel(
                theme=self.theme,
                base_sp=13,
                bold=True,
                color_rgba=self.theme.success_fg if installed else self.theme.primary_blue,
                text=badge,
            )
        )
        card.add_widget(
            AccessibleLabel(
                theme=self.theme,
                base_sp=18,
                bold=True,
                text=str(item["title"]),
            )
        )
        card.add_widget(
            AccessibleLabel(
                theme=self.theme,
                base_sp=14,
                color_rgba=self.theme.text_secondary,
                text=(
                    f"{item['category']} · {item['steps_count']} pasos · "
                    f"Guía v{item['version']} ({item['total_kb']} KB)"
                ),
            )
        )

        btn_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(60), spacing=dp(10))
        pack_id = str(item["pack_id"])
        if installed:
            open_btn = AccessibleButton(
                theme=self.theme,
                bg_rgba=self.theme.primary_blue,
                fg_rgba=self.theme.text_on_dark,
                text="Abrir Guía",
                min_height_dp=56,
            )
            open_btn.bind(on_release=lambda _b, pid=pack_id: self.app_ref.open_guide_pack(pid))
            del_btn = AccessibleButton(
                theme=self.theme,
                bg_rgba=self.theme.surface_tinted,
                fg_rgba=self.theme.text_primary,
                border_rgba=self.theme.border_subtle,
                text="Quitar",
                min_height_dp=56,
                size_hint_x=0.45,
            )
            del_btn.bind(on_release=lambda _b, pid=pack_id: self._uninstall_pack(pid))
            btn_row.add_widget(open_btn)
            btn_row.add_widget(del_btn)
        else:
            dl_btn = AccessibleButton(
                theme=self.theme,
                bg_rgba=self.theme.brand_olive,
                fg_rgba=self.theme.text_on_dark,
                text="Guardar guía en este teléfono",
                min_height_dp=56,
            )
            dl_btn.bind(on_release=lambda _b, pid=pack_id: self._install_pack(pid))
            btn_row.add_widget(dl_btn)

        card.add_widget(btn_row)
        self.packs_container.add_widget(card)

    def _install_pack(self, pack_id: str) -> None:
        manifest = self.app_ref.container.package_manager.install_from_bundled(pack_id)
        self.feedback_lbl.text = (
            f"La guía '{manifest.title}' quedó verificada y guardada ({len(manifest.file_hashes)} archivos) "
            "para usarla sin internet."
        )
        self._refresh_catalog()

    def _uninstall_pack(self, pack_id: str) -> None:
        self.app_ref.container.package_manager.uninstall_pack(pack_id)
        self.feedback_lbl.text = "Guía quitada del almacenamiento de este teléfono."
        self._refresh_catalog()

    def _toggle_offline_mode(self) -> None:
        conn = self.app_ref.container.connectivity
        conn.set_force_offline(not conn.force_offline)
        self.refresh_network_banner()
        self._refresh_catalog()
        if conn.force_offline:
            self.feedback_lbl.text = "Modo Avión activado: el traductor, lector de documentos y guías siguen funcionando."
        else:
            self.feedback_lbl.text = "Modo Avión de prueba desactivado."

    def _run_sync_check(self) -> None:
        c = self.app_ref.container
        c.sync_queue.enqueue(
            "manifest_check",
            {"installed_packs": [p["pack_id"] for p in c.package_manager.list_available_catalog() if p["installed"]]},
        )
        result = c.sync_queue.process_due(
            lambda op: c.cloud_gateway.dispatch_anonymous_sync(op.op_type, op.payload)
        )
        if result["skipped_offline"]:
            self.feedback_lbl.text = (
                "No hay internet ahora: tu solicitud quedó guardada y se revisará cuando tengas señal."
            )
        else:
            self.feedback_lbl.text = (
                f"Revisión completada: {result['succeeded']} actualizadas, "
                f"{result['rescheduled']} en espera para reintentar luego."
            )
        self._refresh_catalog()

    def _speak_offline_status(self) -> None:
        self.app_ref.container.audio_voice.speak(
            "Modo sin conexión. Aquí puedes descargar guías completas de trámites como Acta de Nacimiento, CURP, IMSS y Pensión para usarlas en comunidades sin internet."
        )
