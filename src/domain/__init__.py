"""Modelos puros de dominio y contratos de interfaces entre las 4 capas."""

from src.domain.interfaces import (
    AudioVoicePort,
    CameraCapturePort,
    CloudGatewayPort,
    ConnectivityPort,
    EncryptedRepositoryPort,
    KeyStorePort,
    OCRPort,
)
from src.domain.models import (
    DocumentAnalysisResult,
    DocumentType,
    FSMState,
    FSMTransition,
    LanguageEntry,
    LanguagePack,
    NetworkStatus,
    OfflinePackageManifest,
    ProcedureProgress,
    SyncOperation,
    TranslationResult,
    WorkflowFSM,
)

__all__ = [
    "AudioVoicePort",
    "CameraCapturePort",
    "CloudGatewayPort",
    "ConnectivityPort",
    "DocumentAnalysisResult",
    "DocumentType",
    "EncryptedRepositoryPort",
    "FSMState",
    "FSMTransition",
    "KeyStorePort",
    "LanguageEntry",
    "LanguagePack",
    "NetworkStatus",
    "OCRPort",
    "OfflinePackageManifest",
    "ProcedureProgress",
    "SyncOperation",
    "TranslationResult",
    "WorkflowFSM",
]
