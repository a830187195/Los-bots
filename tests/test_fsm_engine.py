"""Pruebas del motor de Máquina de Estados Finitos (FSM) y persistencia ante reinicios."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.config.settings import APP_PATHS
from src.layer2_edge_ai.fsm_engine import FSMTransitionError, WorkflowFSMEngine
from src.layer3_persistence.database import EncryptedSQLiteRepository
from src.layer3_persistence.keystore import AndroidKeyStoreProvider
from src.layer3_persistence.package_manager import OfflinePackageManager


class TestWorkflowFSMEngine(unittest.TestCase):
    """Verifica transiciones, precondiciones y reanudación exacta tras cierre abrupto."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp_dir = Path(self._tmp.name)
        key = AndroidKeyStoreProvider(self.tmp_dir).get_or_create_master_key()
        self.db_path = self.tmp_dir / "fsm_test.db"
        self.repo = EncryptedSQLiteRepository(self.db_path, key)
        self.key = key
        self.pkg_mgr = OfflinePackageManager(
            bundled_packs_dir=APP_PATHS.packs_dir,
            installed_packs_dir=self.tmp_dir / "installed",
        )
        self.engine = WorkflowFSMEngine(repository=self.repo)

    def tearDown(self) -> None:
        self.repo.close()
        self._tmp.cleanup()

    def test_all_four_bundled_workflows_load_cleanly(self) -> None:
        catalog = self.pkg_mgr.list_available_catalog()
        pack_ids = {item["pack_id"] for item in catalog}
        self.assertEqual(
            pack_ids,
            {"acta_nacimiento", "curp_tramite", "imss_afiliacion", "pension_adulto_mayor"},
        )
        for pid in pack_ids:
            wf = self.pkg_mgr.load_workflow(pid)
            self.assertEqual(wf.initial_state, "S01")
            self.assertGreaterEqual(len(wf.states), 4)

    def test_preconditions_block_and_advance_with_persistence_recovery(self) -> None:
        wf = self.pkg_mgr.load_workflow("acta_nacimiento")
        progress = self.engine.load_or_initialize_progress(wf)
        self.assertEqual(progress.current_state_id, "S01")

        # No puede avanzar sin marcar requisitos de S01
        with self.assertRaises(FSMTransitionError):
            self.engine.advance(wf, progress)

        for item in wf.states["S01"].checklist_items:
            progress = self.engine.toggle_checklist_item(wf, progress, item)

        progress = self.engine.advance(wf, progress)
        self.assertEqual(progress.current_state_id, "S02")

        # No puede avanzar de S02 sin elegir oficina
        with self.assertRaises(FSMTransitionError):
            self.engine.advance(wf, progress)

        progress = self.engine.select_office(progress, wf.states["S02"].office_options[0])
        progress = self.engine.advance(wf, progress)
        self.assertEqual(progress.current_state_id, "S03")

        # Simular cierre abrupto y reapertura con un nuevo repositorio
        self.repo.close()
        reopened_repo = EncryptedSQLiteRepository(self.db_path, self.key)
        self.repo = reopened_repo
        reopened_engine = WorkflowFSMEngine(repository=reopened_repo)
        resumed = reopened_engine.load_or_initialize_progress(wf)
        self.assertEqual(resumed.current_state_id, "S03")
        self.assertEqual(resumed.selected_office, wf.states["S02"].office_options[0])

        # Retroceder a S02 conserva datos y avanzar con exención finaliza en S04
        resumed = reopened_engine.go_back(wf, resumed)
        self.assertEqual(resumed.current_state_id, "S02")
        resumed = reopened_engine.advance(wf, resumed)
        resumed = reopened_engine.set_payment_exempt(resumed, True)
        resumed = reopened_engine.advance(wf, resumed)
        self.assertEqual(resumed.current_state_id, "S04")
        self.assertTrue(wf.states["S04"].is_terminal)
        self.assertEqual(reopened_engine.get_progress_ratio(wf, resumed), 1.0)


if __name__ == "__main__":
    unittest.main()
