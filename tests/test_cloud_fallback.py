"""Pruebas de Capa 4: Certificate Pinning, saneamiento PII en DTOs y fallback offline."""

from __future__ import annotations

import base64
import hashlib
import unittest

from src.config.settings import APP_PATHS
from src.domain.models import NetworkStatus
from src.layer2_edge_ai.translation_engine import (
    DualTranslationEngine,
    LanguagePackRegistry,
)
from src.layer4_cloud.contracts import NMTRequestDTO
from src.layer4_cloud.gateway_client import SecureCloudGatewayClient


class _OnlineStubConnectivity:
    def get_network_status(self) -> NetworkStatus:
        return NetworkStatus.ONLINE_WIFI


class TestCloudGatewayAndFallback(unittest.TestCase):
    """Valida que fallos en la nube nunca bloqueen la app ni filtren PII."""

    def test_nmt_request_dto_redacts_pii_before_network(self) -> None:
        dto = NMTRequestDTO(
            text="Mi CURP es ABCD900101HPLRRS09 y mi nombre es NOMBRE: ANA RUIZ",
            source_lang="es",
            target_lang="nah_puebla",
        )
        safe = dto.to_safe_dict()
        self.assertNotIn("ABCD900101HPLRRS09", safe["text"])
        self.assertIn("[CURP_PROTEGIDA]", safe["text"])

    def test_certificate_pinning_verification(self) -> None:
        fake_der = b"CERTIFICATE_BYTES_PUBLIC_KEY"
        expected_pin = "sha256/" + base64.b64encode(
            hashlib.sha256(fake_der).digest()
        ).decode("ascii")
        client = SecureCloudGatewayClient(
            base_url="https://api.example.invalid/v1",
            pinned_cert_sha256=expected_pin,
        )
        self.assertTrue(client.verify_certificate_der(fake_der))
        self.assertFalse(client.verify_certificate_der(b"ROGUE_MITM_CERT"))

    def test_unreachable_gateway_falls_back_gracefully_to_offline_engine(self) -> None:
        client = SecureCloudGatewayClient(
            base_url="http://non-https-blocked.invalid",  # Esquema inseguro rechazado
            pinned_cert_sha256="sha256/000",
            timeout_seconds=0.2,
        )
        self.assertIsNone(client.translate_nmt("hola", "es", "nah_puebla"))

        reg = LanguagePackRegistry((APP_PATHS.languages_dir,))
        dual = DualTranslationEngine(
            registry=reg,
            connectivity=_OnlineStubConnectivity(),
            cloud_gateway=client,
            allow_cloud=True,
        )
        res = dual.translate("Buenos días, vengo a mi trámite.", "es", "nah_puebla")
        self.assertEqual(res.engine_used, "offline_memory")
        self.assertEqual(res.translated_text, "Niltze, nika' notlahtol")


if __name__ == "__main__":
    unittest.main()
