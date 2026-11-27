"""Pruebas del motor dual de traducción y arquitectura desacoplada de Language Packs."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from src.config.settings import APP_PATHS
from src.domain.models import NetworkStatus
from src.layer2_edge_ai.translation_engine import (
    DualTranslationEngine,
    LanguagePackRegistry,
)
from src.platform_android.connectivity import PlatformConnectivityMonitor


class TestDualTranslationEngine(unittest.TestCase):
    """Verifica traducción offline ES ↔ Náhuatl/Totonaco y extensibilidad sin recompilar."""

    def setUp(self) -> None:
        self.registry = LanguagePackRegistry((APP_PATHS.languages_dir,))
        self.connectivity = PlatformConnectivityMonitor(force_offline=True)
        self.engine = DualTranslationEngine(
            registry=self.registry,
            connectivity=self.connectivity,
            cloud_gateway=None,
            allow_cloud=False,
        )

    def test_exact_offline_translation_spanish_to_nahuatl_and_back(self) -> None:
        res_es_nah = self.engine.translate(
            "Buenos días, vengo a mi trámite.", "es", "nah_puebla"
        )
        self.assertEqual(res_es_nah.translated_text, "Niltze, nika' notlahtol")
        self.assertEqual(res_es_nah.engine_used, "offline_memory")
        self.assertEqual(res_es_nah.confidence, 1.0)

        res_nah_es = self.engine.translate(
            "Niltze, nika' notlahtol", "nah_puebla", "es"
        )
        self.assertIn("Buenos días", res_nah_es.translated_text)
        self.assertEqual(res_nah_es.engine_used, "offline_memory")

    def test_phonetic_fuzzy_translation_offline_for_totonaco(self) -> None:
        res = self.engine.translate(
            "Donde esta la ventanilla", "es", "tot_sierra"
        )
        self.assertEqual(res.engine_used, "offline_fuzzy")
        self.assertIn("Nichu", res.translated_text)
        self.assertGreaterEqual(res.confidence, 0.4)

    def test_decoupled_language_pack_addition_without_code_changes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            lang_dir = Path(tmp)
            maya_pack = {
                "lang_code": "yua_maya",
                "display_name": "Maya Yucateco",
                "variant_region": "Península",
                "version": "1.0.0",
                "validation_status": "demo_pendiente_validacion_comunitaria",
                "entries": [
                    {
                        "entry_id": "yua_001",
                        "spanish": "Buenos días",
                        "spanish_simple": "Buenos días",
                        "indigenous_text": "Ma'alob k'iin",
                        "phonetic_guide": "Ma-a-lob kin",
                        "domain_tag": "saludo",
                        "keywords": ["hola", "buenos dias"],
                    }
                ],
            }
            (lang_dir / "yua_maya.json").write_text(
                json.dumps(maya_pack), encoding="utf-8"
            )
            custom_reg = LanguagePackRegistry((APP_PATHS.languages_dir, lang_dir))
            self.assertIsNotNone(custom_reg.get_pack("yua_maya"))
            conn_off = PlatformConnectivityMonitor(force_offline=True)
            engine = DualTranslationEngine(
                custom_reg,
                connectivity=conn_off,
            )
            self.assertEqual(conn_off.get_network_status(), NetworkStatus.OFFLINE)
            res = engine.translate("Buenos días", "es", "yua_maya")
            self.assertEqual(res.translated_text, "Ma'alob k'iin")


if __name__ == "__main__":
    unittest.main()
