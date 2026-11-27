"""Pruebas de Privacidad por Diseño (PII/EXIF), OCR local y simplificador burocrático."""

from __future__ import annotations

import unittest

from src.domain.models import DocumentType
from src.layer2_edge_ai.document_interpreter import DocumentInterpreter
from src.layer2_edge_ai.ocr_pipeline import LocalOCREngine, _compute_otsu_threshold
from src.layer2_edge_ai.privacy import (
    PIIRedactor,
    secure_wipe_buffer,
    strip_image_metadata,
)


class TestPrivacyAndDocumentOCR(unittest.TestCase):
    """Valida redacción PII, limpieza EXIF, Otsu y simplificación ciudadana."""

    def test_pii_redactor_masks_curp_ine_nss_names_and_folios(self) -> None:
        raw = (
            "NOMBRE: JUAN PEREZ LOPEZ\n"
            "CURP: PELJ850101HPLRRS02\n"
            "CLAVE ELECTOR: PRLPJN85010121H100\n"
            "NSS: 12345678901\n"
            "FOLIO: ACTA-9928412\n"
            "CORREO: juan@ejemplo.mx"
        )
        redacted = PIIRedactor.redact(raw)
        self.assertNotIn("PELJ850101HPLRRS02", redacted)
        self.assertNotIn("JUAN PEREZ LOPEZ", redacted)
        self.assertNotIn("PRLPJN85010121H100", redacted)
        self.assertNotIn("12345678901", redacted)
        self.assertNotIn("ACTA-9928412", redacted)
        self.assertNotIn("juan@ejemplo.mx", redacted)
        self.assertIn("[CURP_PROTEGIDA]", redacted)
        self.assertIn("[NOMBRE_PROTEGIDO]", redacted)
        self.assertIn("****8412", redacted)

    def test_strip_jpeg_exif_segments_without_external_deps(self) -> None:
        # JPEG mínimo: SOI + APP1 (EXIF simulado) + SOS + datos + EOI
        exif_payload = b"Exif\x00\x00GPS_LAT_19_04"
        app1_len = (len(exif_payload) + 2).to_bytes(2, "big")
        fake_jpeg = (
            b"\xff\xd8"
            + b"\xff\xe1" + app1_len + exif_payload
            + b"\xff\xda\x00\x08\x01\x01\x00\x00\x3f\x00"
            + b"\x11\x22\x33\xff\xd9"
        )
        cleaned = strip_image_metadata(fake_jpeg)
        self.assertTrue(cleaned.startswith(b"\xff\xd8"))
        self.assertNotIn(b"GPS_LAT", cleaned)
        self.assertNotIn(b"\xff\xe1", cleaned)

    def test_secure_wipe_buffer_zeros_volatile_ram(self) -> None:
        buf = bytearray(b"SENSITIVE_DOCUMENT_BYTES")
        secure_wipe_buffer(buf)
        self.assertEqual(len(buf), 0)

    def test_otsu_threshold_bimodal_histogram(self) -> None:
        hist = [0] * 256
        hist[30] = 500
        hist[220] = 500
        threshold = _compute_otsu_threshold(hist)
        self.assertGreaterEqual(threshold, 30)
        self.assertLess(threshold, 220)

    def test_document_classification_and_bureaucratic_simplification(self) -> None:
        interpreter = DocumentInterpreter()
        ocr = LocalOCREngine()
        sample = (
            "CITATORIO OFICIAL. FOLIO: DGA-448120. "
            "Se requiere acreditar personalidad jurídica mediante instrumento público "
            "o identificación oficial vigente y presentar en original y copia fotostática legible "
            "antes del 15/12/2026 con pago de $185.00 MXN."
        )
        boxes = ocr.extract_text_boxes(b"", hint_text=sample)
        result = interpreter.analyze_ocr_boxes(boxes)

        self.assertEqual(result.document_type, DocumentType.CITATORIO_OFICIAL)
        self.assertIn("15/12/2026", result.detected_dates)
        self.assertTrue(any("185.00" in amt for amt in result.detected_amounts))
        self.assertEqual(result.detected_folios_masked, ("******8120",))
        self.assertTrue(
            any("credencial INE o pasaporte" in simple for _f, simple in result.simplified_clauses)
        )


if __name__ == "__main__":
    unittest.main()
