"""Pruebas de cifrado AES-256-GCM, paquetes .mtjpack, deltas SHA-256 y SyncQueue."""

from __future__ import annotations

import hashlib
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from src.config.settings import APP_PATHS
from src.domain.models import NetworkStatus, OfflinePackageManifest
from src.layer3_persistence.database import AES256Cipher, EncryptedSQLiteRepository
from src.layer3_persistence.keystore import AndroidKeyStoreProvider
from src.layer3_persistence.package_manager import OfflinePackageManager
from src.layer3_persistence.sync_queue import SmartSyncQueue
from src.platform_android.connectivity import PlatformConnectivityMonitor


class TestPersistenceAndDeltaSync(unittest.TestCase):
    """Verifica cifrado en reposo, verificación SHA-256, deltas y backoff exponencial."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp_dir = Path(self._tmp.name)
        self.master_key = AndroidKeyStoreProvider(self.tmp_dir).get_or_create_master_key()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_aes256_encrypt_decrypt_and_tamper_rejection(self) -> None:
        cipher = AES256Cipher(self.master_key)
        secret = "Estado S02 - Registro Civil Puebla"
        token = cipher.encrypt_text(secret)
        self.assertNotIn("Registro Civil", token)
        self.assertEqual(cipher.decrypt_text(token), secret)

        # Manipular el último carácter del token debe fallar autenticación
        tampered = token[:-2] + ("A" if token[-2] != "A" else "B") + token[-1]
        with self.assertRaises(Exception):
            cipher.decrypt_text(tampered)

    def test_mtjpack_packaging_sha256_verification_and_delta_patching(self) -> None:
        mgr = OfflinePackageManager(
            bundled_packs_dir=APP_PATHS.packs_dir,
            installed_packs_dir=self.tmp_dir / "installed",
        )
        manifest_v1 = mgr.install_from_bundled("curp_tramite")
        self.assertTrue(mgr.is_installed("curp_tramite"))

        # Simular actualización remota donde solo cambia workflow.json y un recurso sigue intacto
        installed_dir = self.tmp_dir / "installed" / "curp_tramite"
        (installed_dir / "extra_audio.opus").write_bytes(b"UNCHANGED_AUDIO_BYTES")
        # Añadir archivo intacto al manifiesto local v1
        local_hashes = dict(manifest_v1.file_hashes)
        local_hashes["extra_audio.opus"] = hashlib.sha256(b"UNCHANGED_AUDIO_BYTES").hexdigest()
        local_m = OfflinePackageManifest(
            pack_id="curp_tramite",
            title=manifest_v1.title,
            version="1.0.0",
            description="",
            total_bytes=manifest_v1.total_bytes,
            file_hashes=local_hashes,
        )

        new_wf_bytes = (installed_dir / "workflow.json").read_bytes().replace(b"1.0.0", b"1.1.0")
        remote_hashes = dict(local_hashes)
        remote_hashes["workflow.json"] = hashlib.sha256(new_wf_bytes).hexdigest()
        remote_m = OfflinePackageManifest(
            pack_id="curp_tramite",
            title=manifest_v1.title,
            version="1.1.0",
            description="",
            total_bytes=len(new_wf_bytes),
            file_hashes=remote_hashes,
        )

        plan = mgr.compute_delta_plan(local_m, remote_m)
        self.assertEqual(plan.files_to_download, ("workflow.json",))
        self.assertIn("extra_audio.opus", plan.unchanged_files)
        self.assertIn("assets/svg/documents.svg", plan.unchanged_files)
        self.assertGreaterEqual(plan.savings_ratio, 0.8)

        mgr.apply_delta_patch("curp_tramite", {"workflow.json": new_wf_bytes}, remote_m)
        updated_m = mgr.get_installed_manifest("curp_tramite")
        self.assertIsNotNone(updated_m)
        assert updated_m is not None
        self.assertEqual(updated_m.version, "1.1.0")

    def test_corrupt_mtjpack_sha256_is_rejected(self) -> None:
        mgr = OfflinePackageManager(
            bundled_packs_dir=APP_PATHS.packs_dir,
            installed_packs_dir=self.tmp_dir / "installed_bad",
        )
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr(
                "manifest.json",
                json.dumps(
                    {
                        "pack_id": "bad_pack",
                        "title": "Bad",
                        "version": "1.0.0",
                        "total_bytes": 4,
                        "file_hashes": {"workflow.json": "0" * 64},
                    }
                ),
            )
            zf.writestr("workflow.json", "{}")
        with self.assertRaises(ValueError):
            mgr.install_mtjpack_bytes(buf.getvalue())

    def test_smart_sync_queue_exponential_backoff_and_offline_skip(self) -> None:
        repo = EncryptedSQLiteRepository(self.tmp_dir / "sync.db", self.master_key)
        try:
            conn = PlatformConnectivityMonitor(force_offline=True)
            queue = SmartSyncQueue(repo, conn, base_delay_seconds=10.0)
            queue.enqueue("telemetry", {"event": "step_done"}, now_epoch=1000.0)

            res_off = queue.process_due(lambda _op: True, now_epoch=1000.0)
            self.assertEqual(res_off["skipped_offline"], 1)
            self.assertEqual(queue.pending_count(), 1)

            # Activar red simulada (WiFi) manteniendo caché activa sin socket real
            conn.force_offline = False
            conn._cached_status = NetworkStatus.ONLINE_WIFI
            conn._last_checked = 10**12

            res_fail = queue.process_due(lambda _op: False, now_epoch=1000.0)
            self.assertEqual(res_fail["rescheduled"], 1)
            self.assertEqual(queue.calculate_backoff_seconds(1), 10.0)
            self.assertEqual(queue.calculate_backoff_seconds(2), 20.0)
            self.assertEqual(queue.calculate_backoff_seconds(3), 40.0)

            # Antes de next_retry_epoch (1010.0) no debe procesarse aún
            due_early = repo.list_due_sync_operations(1005.0)
            self.assertEqual(len(due_early), 0)

            # En 1010.0 sí vence y se completa
            res_ok = queue.process_due(lambda _op: True, now_epoch=1010.0)
            self.assertEqual(res_ok["succeeded"], 1)
            self.assertEqual(queue.pending_count(), 0)
        finally:
            repo.close()


if __name__ == "__main__":
    unittest.main()
