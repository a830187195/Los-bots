"""Contratos DTO para la comunicación desacoplada con API Gateway y CDN."""

from __future__ import annotations

from dataclasses import dataclass

from src.layer2_edge_ai.privacy import PIIRedactor


@dataclass(frozen=True)
class NMTRequestDTO:
    """Solicitud de traducción neuronal (NMT) con saneamiento previo de PII."""

    text: str
    source_lang: str
    target_lang: str
    dialect_region: str = "sierra_norte_puebla"

    def to_safe_dict(self) -> dict[str, str]:
        """Garantiza que ningún dato personal salga del dispositivo."""
        return {
            "text": PIIRedactor.redact(self.text),
            "source_lang": self.source_lang,
            "target_lang": self.target_lang,
            "dialect_region": self.dialect_region,
        }


@dataclass(frozen=True)
class NMTResponseDTO:
    """Respuesta estructurada del microservicio NMT (PyTorch / Transformers)."""

    translated_text: str
    phonetic_guide: str
    confidence: float
    model_version: str


@dataclass(frozen=True)
class TelemetryEventDTO:
    """Evento analítico estrictamente anonimizado para métricas agregadas."""

    event_name: str
    pack_id: str
    step_state: str
    app_version: str

    def to_safe_dict(self) -> dict[str, str]:
        """Serializa únicamente metadatos anónimos sin identificadores de usuario."""
        return {
            "event_name": self.event_name,
            "pack_id": self.pack_id,
            "step_state": self.step_state,
            "app_version": self.app_version,
        }
