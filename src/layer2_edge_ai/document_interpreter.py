"""Fase 3 y 4: Clasificador documental, extractor seguro y simplificador ciudadano."""

from __future__ import annotations

import re
import time
from typing import Final

from src.domain.models import DocumentAnalysisResult, DocumentType, OCRBoundingBox
from src.layer2_edge_ai.privacy import PIIRedactor

# Reglas de clasificación local supervisada por palabras clave y peso semántico
_DOCUMENT_SIGNATURES: Final[dict[DocumentType, tuple[tuple[str, float], ...]]] = {
    DocumentType.ACTA_NACIMIENTO: (
        ("acta de nacimiento", 5.0),
        ("registro civil", 4.0),
        ("oficialia", 2.5),
        ("oficialía", 2.5),
        ("estados unidos mexicanos", 1.5),
        ("lugar de nacimiento", 3.0),
        ("fecha de registro", 2.5),
        ("datos de filiacion", 2.5),
        ("filiación", 2.5),
    ),
    DocumentType.CURP: (
        ("clave unica de registro de poblacion", 5.0),
        ("clave única de registro de población", 5.0),
        ("curp", 4.0),
        ("renapo", 3.5),
        ("constancia", 2.0),
        ("secretaria de gobernacion", 2.0),
        ("secretaría de gobernación", 2.0),
    ),
    DocumentType.INE: (
        ("instituto nacional electoral", 5.0),
        ("credencial para votar", 5.0),
        ("clave de elector", 4.0),
        ("vigencia", 2.0),
        ("seccion", 2.0),
        ("sección", 2.0),
        ("emision", 1.5),
    ),
    DocumentType.COMPROBANTE_DOMICILIO: (
        ("comision federal de electricidad", 5.0),
        ("comisión federal de electricidad", 5.0),
        ("cfe", 3.5),
        ("agua potable", 4.0),
        ("recibo", 2.5),
        ("total a pagar", 3.0),
        ("periodo facturado", 3.0),
        ("fecha limite de pago", 3.0),
        ("fecha límite de pago", 3.0),
        ("telmex", 3.5),
    ),
    DocumentType.COMPROBANTE_IMSS: (
        ("instituto mexicano del seguro social", 5.0),
        ("imss", 4.5),
        ("vigencia de derechos", 4.0),
        ("numero de seguridad social", 4.0),
        ("número de seguridad social", 4.0),
        ("nss", 3.5),
        ("umf", 3.0),
        ("unidad de medicina familiar", 3.5),
    ),
    DocumentType.CITATORIO_OFICIAL: (
        ("acreditar personalidad juridica", 5.0),
        ("acreditar personalidad jurídica", 5.0),
        ("citatorio", 4.5),
        ("comparecer", 4.0),
        ("requerimiento", 3.5),
        ("termino perentorio", 3.5),
        ("término perentorio", 3.5),
        ("apercibimiento", 3.5),
        ("oficio", 2.5),
        ("ventanilla", 2.0),
        ("original y copia", 2.5),
    ),
}

# Mapa semántico: jerga burocrática -> lenguaje ciudadano claro
_BUREAUCRATIC_SIMPLIFICATION_MAP: Final[tuple[tuple[str, str, str], ...]] = (
    (
        r"acreditar\s+personalidad\s+jur[ií]dica.*?(?:identificaci[oó]n\s+oficial\s+vigente|instrumento\s+p[uú]blico)?",
        "Acreditar personalidad jurídica mediante instrumento público o identificación oficial vigente.",
        "Muestra un documento oficial que pruebe quién eres (como tu credencial INE o pasaporte).",
    ),
    (
        r"presentar\s+(?:en\s+)?original\s+y\s+copia(?:\s+fotost[aá]tica)?(?:\s+legible)?",
        "Presentar en original y copia fotostática legible.",
        "Lleva tu papel original para que lo revisen y entrega una fotocopia clara. No entregues tu original.",
    ),
    (
        r"en\s+un\s+t[eé]rmino\s+perentorio\s+de\s+(\d+)\s+d[ií]as\s+h[aá]biles",
        "En un término perentorio de días hábiles.",
        "Tienes un plazo máximo (contando solo de lunes a viernes, sin días festivos) para entregar esto sin perder tu turno.",
    ),
    (
        r"bajo\s+protesta\s+de\s+decir\s+verdad",
        "Bajo protesta de decir verdad.",
        "Declaras que todo lo que estás diciendo o escribiendo es completamente cierto.",
    ),
    (
        r"subsanar\s+(?:las\s+)?inconsistencias(?:\s+registrales)?",
        "Subsanar inconsistencias registrales.",
        "Corregir un error o dato distinto en tus papeles (por ejemplo, una letra mal escrita en tu nombre o fecha).",
    ),
    (
        r"constancia\s+de\s+vigencia\s+de\s+derechos",
        "Constancia de vigencia de derechos.",
        "Un papel gratuito que confirma que hoy sí tienes servicio médico activo en el IMSS.",
    ),
    (
        r"enterar\s+(?:el\s+)?pago\s+de\s+derechos",
        "Enterar el pago de derechos.",
        "Pagar el costo del trámite en la caja o banco autorizado y guardar tu comprobante.",
    ),
    (
        r"exenci[oó]n\s+de\s+tarifa|condonaci[oó]n\s+de\s+derechos",
        "Exención o condonación de derechos.",
        "No tienes que pagar este trámite si cumples los requisitos de apoyo gratuito.",
    ),
    (
        r"comparecer\s+(?:de\s+manera\s+)?personal",
        "Comparecer de manera personal.",
        "Debes ir tú mismo en persona a la oficina; no puede ir alguien más por ti salvo con carta poder.",
    ),
    (
        r"cotejo\s+documental",
        "Cotejo documental.",
        "El personal de la ventanilla revisará que tu copia sea igualita a tu documento original y te devolverá el original.",
    ),
)

_DATE_REGEX: Final[re.Pattern[str]] = re.compile(
    r"\b(?:\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}|\d{1,2}\s+de\s+(?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\s+(?:de\s+)?\d{4})\b",
    re.IGNORECASE,
)
_AMOUNT_REGEX: Final[re.Pattern[str]] = re.compile(
    r"\$\s?\d{1,3}(?:,\d{3})*(?:\.\d{2})?(?:\s*(?:MXN|M\.N\.|pesos))?",
    re.IGNORECASE,
)
_FOLIO_CAPTURE_REGEX: Final[re.Pattern[str]] = re.compile(
    r"\b(?:FOLIO|ACTA|IDENTIFICADOR|NO\.)\s*[:#]?\s*([A-Z0-9\-]{5,20})\b",
    re.IGNORECASE,
)

_DOCUMENT_PROFILES: Final[dict[DocumentType, dict[str, str]]] = {
    DocumentType.ACTA_NACIMIENTO: {
        "title": "Acta de Nacimiento",
        "pictogram": "document_acta",
        "purpose": "Acredita tu identidad legal, fecha y lugar de nacimiento en México.",
        "badge": "CONSERVAR ORIGINAL Y ENTREGAR COPIA",
        "details": "Guarda siempre el acta original en un lugar seguro. Para casi todos los trámites solo entregas una copia legible.",
        "pack_id": "acta_nacimiento",
    },
    DocumentType.CURP: {
        "title": "Constancia de CURP",
        "pictogram": "document_curp",
        "purpose": "Es tu clave personal única para inscribirte en escuelas, hospitales y programas sociales.",
        "badge": "IMPRIMIR COPIA GRATUITA",
        "details": "La CURP no vence y es gratuita. Verifica que tu nombre y fecha de nacimiento coincidan exactamente con tu acta.",
        "pack_id": "curp_tramite",
    },
    DocumentType.INE: {
        "title": "Credencial para Votar (INE)",
        "pictogram": "document_ine",
        "purpose": "Sirve como identificación oficial vigente para comprobar quién eres y tu domicilio.",
        "badge": "CONSERVAR ORIGINAL Y ENTREGAR COPIA AMBOS LADOS",
        "details": "Nunca dejes tu credencial original retenida. Entrega copia por ambos lados en la misma hoja.",
        "pack_id": "acta_nacimiento",
    },
    DocumentType.COMPROBANTE_DOMICILIO: {
        "title": "Comprobante de Domicilio",
        "pictogram": "document_home",
        "purpose": "Comprueba la dirección donde vives actualmente (debe tener menos de 3 meses de antigüedad).",
        "badge": "REVISAR FECHA Y ENTREGAR COPIA",
        "details": "No necesita estar a tu nombre en la mayoría de oficinas, pero sí debe verse clara la dirección y la fecha reciente.",
        "pack_id": "pension_adulto_mayor",
    },
    DocumentType.COMPROBANTE_IMSS: {
        "title": "Documento o Vigencia IMSS",
        "pictogram": "document_imss",
        "purpose": "Confirma tu registro en el Seguro Social y la clínica (UMF) que te corresponde.",
        "badge": "PRESENTAR EN VENTANILLA DE CLÍNICA",
        "details": "Lleva este papel junto con tu identificación oficial y tu CURP cuando acudas a tu clínica del IMSS.",
        "pack_id": "imss_afiliacion",
    },
    DocumentType.CITATORIO_OFICIAL: {
        "title": "Oficio o Citatorio Oficial",
        "pictogram": "document_official",
        "purpose": "Es un aviso formal de una oficina pública que te pide acudir o entregar un papel específico.",
        "badge": "ATENDER ANTES DE LA FECHA LÍMITE",
        "details": "Revisa la explicación sencilla abajo para saber exactamente qué papeles llevar y en qué fecha presentarte.",
        "pack_id": "acta_nacimiento",
    },
    DocumentType.DESCONOCIDO: {
        "title": "Documento Administrativo",
        "pictogram": "document_generic",
        "purpose": "No se reconoció un formato estándar, pero extrajimos fechas, montos y frases clave para ayudarte.",
        "badge": "LLEVAR ORIGINAL PARA REVISIÓN EN VENTANILLA",
        "details": "Si el texto está borroso, intenta tomar la foto en un lugar con buena luz y sin sombras.",
        "pack_id": "",
    },
}


class DocumentInterpreter:
    """Clasifica documentos, simplifica lenguaje burocrático y protege PII en Edge."""

    def analyze_ocr_boxes(self, boxes: list[OCRBoundingBox]) -> DocumentAnalysisResult:
        """Analiza bloques OCR en memoria volátil y genera explicación ciudadana."""
        raw_text = "\n".join(box.text for box in boxes if box.text.strip())
        return self.analyze_text(raw_text)

    def analyze_text(self, raw_text: str) -> DocumentAnalysisResult:
        """Clasifica el texto OCR y produce traducción ciudadana sin almacenar PII."""
        started = time.perf_counter()
        normalized = _normalize_for_matching(raw_text)

        doc_type, confidence = self._classify(normalized)
        profile = _DOCUMENT_PROFILES[doc_type]

        dates = tuple(dict.fromkeys(_DATE_REGEX.findall(raw_text)))[:5]
        amounts = tuple(dict.fromkeys(_AMOUNT_REGEX.findall(raw_text)))[:5]
        folios_masked = tuple(
            dict.fromkeys(
                PIIRedactor.mask_identifier(m)
                for m in _FOLIO_CAPTURE_REGEX.findall(raw_text)
            )
        )[:4]

        simplified = self.simplify_bureaucratic_text(raw_text)
        elapsed_ms = round((time.perf_counter() - started) * 1000.0, 2)

        action_details = profile["details"]
        if amounts:
            action_details += f" Monto detectado: {amounts[0]}."
        if dates:
            action_details += f" Fecha detectada: {dates[0]}."

        return DocumentAnalysisResult(
            document_type=doc_type,
            document_title=profile["title"],
            pictogram_id=profile["pictogram"],
            purpose_citizen=profile["purpose"],
            action_badge=profile["badge"],
            action_details=action_details,
            detected_dates=dates,
            detected_amounts=amounts,
            detected_folios_masked=folios_masked,
            simplified_clauses=simplified,
            recommended_pack_id=profile["pack_id"],
            confidence=confidence,
            processing_ms=elapsed_ms,
        )

    def simplify_bureaucratic_text(self, raw_text: str) -> tuple[tuple[str, str], ...]:
        """Detecta frases legales densas y devuelve pares (jerga, explicación ciudadana)."""
        if not raw_text:
            return ()
        matches: list[tuple[str, str]] = []
        seen_citizens: set[str] = set()
        for pattern_str, formal_label, citizen_text in _BUREAUCRATIC_SIMPLIFICATION_MAP:
            if re.search(pattern_str, raw_text, flags=re.IGNORECASE | re.DOTALL):
                if citizen_text not in seen_citizens:
                    seen_citizens.add(citizen_text)
                    matches.append((formal_label, citizen_text))
        return tuple(matches)

    def _classify(self, normalized_text: str) -> tuple[DocumentType, float]:
        if not normalized_text:
            return DocumentType.DESCONOCIDO, 0.0

        scores: dict[DocumentType, float] = {}
        for doc_type, keywords in _DOCUMENT_SIGNATURES.items():
            score = 0.0
            for keyword, weight in keywords:
                if keyword in normalized_text:
                    score += weight
            if score > 0:
                scores[doc_type] = score

        if not scores:
            return DocumentType.DESCONOCIDO, 0.25

        best_type = max(scores, key=lambda dt: scores[dt])
        best_score = scores[best_type]
        confidence = round(min(0.99, 0.45 + (best_score / 12.0)), 2)
        return best_type, confidence


def _normalize_for_matching(text: str) -> str:
    lowered = text.lower()
    lowered = re.sub(r"\s+", " ", lowered)
    return lowered.strip()
