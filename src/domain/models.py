"""Entidades de dominio inmutables y estructuras declarativas del sistema."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class DocumentType(str, Enum):
    """Tipologías de documentos oficiales soportadas por el clasificador Edge."""

    ACTA_NACIMIENTO = "acta_nacimiento"
    CURP = "curp"
    INE = "ine"
    COMPROBANTE_DOMICILIO = "comprobante_domicilio"
    CITATORIO_OFICIAL = "citatorio_oficial"
    COMPROBANTE_IMSS = "comprobante_imss"
    DESCONOCIDO = "desconocido"


class NetworkStatus(str, Enum):
    """Estado de enlace de red monitoreado sin bloquear la interfaz."""

    OFFLINE = "offline"
    ONLINE_CELLULAR = "online_cellular"
    ONLINE_WIFI = "online_wifi"


class SyncStatus(str, Enum):
    """Estado de las tareas asíncronas en la cola de sincronización."""

    PENDING = "pending"
    RETRY_WAIT = "retry_wait"
    COMPLETED = "completed"
    FAILED_PERMANENT = "failed_permanent"


@dataclass(frozen=True)
class LanguageEntry:
    """Entrada bilingüe Español ↔ Lengua Originaria con guía fonética y audio."""

    entry_id: str
    spanish: str
    spanish_simple: str
    indigenous_text: str
    phonetic_guide: str
    domain_tag: str
    audio_clip: str = ""
    keywords: tuple[str, ...] = ()


@dataclass(frozen=True)
class LanguagePack:
    """Paquete lingüístico desacoplado cargable sin recompilar la aplicación."""

    lang_code: str
    display_name: str
    variant_region: str
    version: str
    validation_status: str
    entries: tuple[LanguageEntry, ...] = ()


@dataclass(frozen=True)
class TranslationResult:
    """Resultado de traducción dual con trazabilidad del motor utilizado."""

    source_text: str
    translated_text: str
    phonetic_guide: str
    source_lang: str
    target_lang: str
    engine_used: str  # "offline_memory", "offline_fuzzy", "cloud_nmt"
    confidence: float
    audio_clip: str = ""
    citizen_note: str = ""


@dataclass(frozen=True)
class OCRBoundingBox:
    """Bloque de texto extraído por el motor OCR local con sus coordenadas."""

    text: str
    x: int
    y: int
    width: int
    height: int
    confidence: float


@dataclass(frozen=True)
class DocumentAnalysisResult:
    """Salida en lenguaje ciudadano generada localmente sin filtrar PII."""

    document_type: DocumentType
    document_title: str
    pictogram_id: str
    purpose_citizen: str
    action_badge: str
    action_details: str
    detected_dates: tuple[str, ...] = ()
    detected_amounts: tuple[str, ...] = ()
    detected_folios_masked: tuple[str, ...] = ()
    simplified_clauses: tuple[tuple[str, str], ...] = ()
    recommended_pack_id: str = ""
    confidence: float = 0.0
    processing_ms: float = 0.0


@dataclass(frozen=True)
class FSMTransition:
    """Transición declarativa condicionada entre estados de un trámite."""

    target_state: str
    condition: str  # e.g., "checklist_complete", "office_selected", "always"
    label: str


@dataclass(frozen=True)
class FSMState:
    """Nodo atómico de la Máquina de Estados Finitos de un trámite."""

    state_id: str
    step_number: int
    title: str
    citizen_instruction: str
    pictogram_id: str
    checklist_items: tuple[str, ...] = ()
    translations: dict[str, str] = field(default_factory=dict)
    audio_script_es: str = ""
    audio_clips: dict[str, str] = field(default_factory=dict)
    office_options: tuple[str, ...] = ()
    next_transition: FSMTransition | None = None
    prev_state: str | None = None
    is_terminal: bool = False


@dataclass(frozen=True)
class WorkflowFSM:
    """Definición completa de un trámite guiado compatible con .mtjpack."""

    pack_id: str
    title: str
    category: str
    version: str
    estimated_time: str
    cost_summary: str
    initial_state: str
    states: dict[str, FSMState]


@dataclass
class ProcedureProgress:
    """Estado persistido localmente para reanudar trámites sin pérdida."""

    pack_id: str
    current_state_id: str
    completed_checklist: dict[str, list[str]] = field(default_factory=dict)
    selected_office: str = ""
    payment_exempt: bool = False
    updated_at_iso: str = ""


@dataclass(frozen=True)
class OfflinePackageManifest:
    """Manifiesto con hashes SHA-256 para verificación de integridad y deltas."""

    pack_id: str
    title: str
    version: str
    description: str
    total_bytes: int
    file_hashes: dict[str, str]
    languages_included: tuple[str, ...] = ("es", "nah_puebla", "tot_sierra")
    signature_hmac: str = ""


@dataclass
class SyncOperation:
    """Elemento persistente en la cola de sincronización con backoff exponencial."""

    op_id: str
    op_type: str
    payload: dict[str, Any]
    status: SyncStatus = SyncStatus.PENDING
    attempt_count: int = 0
    next_retry_epoch: float = 0.0
    created_at_iso: str = ""
    last_error: str = ""
