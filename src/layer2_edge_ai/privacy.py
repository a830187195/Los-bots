"""Privacidad por Diseño (Privacy by Design): anonimización PII y limpieza en RAM."""

from __future__ import annotations

import gc
import io
import re
from typing import Final

# Patrones de PII mexicanos protegidos antes de cualquier registro o diagnóstico
_CURP_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"\b[A-Z]{4}\d{6}[HM][A-Z]{2}[B-DF-HJ-NP-TV-Z]{3}[A-Z0-9]\d\b",
    re.IGNORECASE,
)
_RFC_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"\b[A-ZÑ&]{3,4}\d{6}[A-Z0-9]{3}\b",
    re.IGNORECASE,
)
_CLAVE_ELECTOR_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"\b[A-Z]{6}\d{8}[HM]\d{3}\b",
    re.IGNORECASE,
)
_NSS_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"\b(?:NSS|SEGURIDAD SOCIAL|AFILIACI[ÓO]N)[:\s#]*(\d{10,11})\b",
    re.IGNORECASE,
)
_NAME_LINE_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"(?im)^((?:NOMBRE|TITULAR|CIUDADAN[OA]|INTERESAD[OA]|C\.)\s*[:\-]?\s*)([A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑáéíóúñ\s]{4,60})$"
)
_FOLIO_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"\b(?:FOLIO|ACTA|IDENTIFICADOR|CIC|OCR)\s*(?:NO\.?|N[ÚU]M\.?|#|:)?\s*([A-Z0-9\-]{6,20})\b",
    re.IGNORECASE,
)
_PHONE_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"(?<!\d)(?:\+?52\s?)?(?:\(?\d{2,3}\)?[\s\-]?)?\d{3,4}[\s\-]?\d{4}(?!\d)"
)
_EMAIL_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"
)


class PIIRedactor:
    """Elimina o enmascara datos personales identificables antes de registrar eventos."""

    @staticmethod
    def redact(text: str) -> str:
        """Reemplaza identificadores personales (CURP, INE, NSS, nombres) por etiquetas."""
        if not text:
            return ""
        sanitized = _CURP_PATTERN.sub("[CURP_PROTEGIDA]", text)
        sanitized = _CLAVE_ELECTOR_PATTERN.sub("[CLAVE_INE_PROTEGIDA]", sanitized)
        sanitized = _RFC_PATTERN.sub("[RFC_PROTEGIDO]", sanitized)
        sanitized = _NSS_PATTERN.sub(
            lambda m: m.group(0).replace(m.group(1), "[NSS_PROTEGIDO]"), sanitized
        )
        sanitized = _NAME_LINE_PATTERN.sub(r"\1[NOMBRE_PROTEGIDO]", sanitized)
        sanitized = _FOLIO_PATTERN.sub(
            lambda m: m.group(0).replace(m.group(1), _mask_tail(m.group(1))), sanitized
        )
        sanitized = _EMAIL_PATTERN.sub("[CORREO_PROTEGIDO]", sanitized)
        sanitized = _PHONE_PATTERN.sub("[TELEFONO_PROTEGIDO]", sanitized)
        return sanitized

    @staticmethod
    def mask_identifier(value: str) -> str:
        """Conserva únicamente los últimos 4 dígitos para verificación visual segura."""
        return _mask_tail(value)


def _mask_tail(value: str) -> str:
    clean = value.strip()
    if len(clean) <= 4:
        return "****"
    return ("*" * (len(clean) - 4)) + clean[-4:]


def strip_image_metadata(image_bytes: bytes) -> bytes:
    """Elimina metadatos EXIF/GPS/XMP en memoria volátil sin guardar archivos temporales."""
    if not image_bytes:
        return b""

    try:
        from PIL import Image, ImageOps  # type: ignore import-not-found

        with Image.open(io.BytesIO(image_bytes)) as img:
            img_oriented = ImageOps.exif_transpose(img)
            clean_img = Image.new(img_oriented.mode, img_oriented.size)
            clean_img.putdata(list(img_oriented.getdata()))
            out_buf = io.BytesIO()
            fmt = (img.format or "PNG").upper()
            if fmt not in {"JPEG", "PNG", "WEBP"}:
                fmt = "PNG"
            if fmt == "JPEG" and clean_img.mode not in {"RGB", "L"}:
                clean_img = clean_img.convert("RGB")
            clean_img.save(out_buf, format=fmt)
            return out_buf.getvalue()
    except ImportError:
        return _strip_jpeg_app_segments(image_bytes)
    except Exception:
        return _strip_jpeg_app_segments(image_bytes)


def _strip_jpeg_app_segments(data: bytes) -> bytes:
    """Elimina segmentos APP1..APP15 y COM en imágenes JPEG sin depender de librerías C."""
    if len(data) < 4 or data[:2] != b"\xff\xd8":
        return data

    out = bytearray(b"\xff\xd8")
    idx = 2
    length = len(data)
    while idx < length - 1:
        if data[idx] != 0xFF:
            out.extend(data[idx:])
            break
        marker = data[idx + 1]
        if marker == 0xDA:  # Start of Scan: copiar resto del flujo de imagen
            out.extend(data[idx:])
            break
        if marker in (0xD8, 0xD9, 0x00) or (0xD0 <= marker <= 0xD7):
            out.extend(data[idx : idx + 2])
            idx += 2
            continue
        if idx + 4 > length:
            break
        seg_len = int.from_bytes(data[idx + 2 : idx + 4], "big")
        if seg_len < 2 or idx + 2 + seg_len > length:
            break
        # Descartar APP1 (EXIF/XMP), APP2..APP15 y COM (0xFE)
        if not ((0xE1 <= marker <= 0xEF) or marker == 0xFE):
            out.extend(data[idx : idx + 2 + seg_len])
        idx += 2 + seg_len
    return bytes(out)


def secure_wipe_buffer(buffer: bytearray | None) -> None:
    """Sobrescribe un buffer mutable en RAM y sugiere recolección inmediata."""
    if buffer is not None:
        for i in range(len(buffer)):
            buffer[i] = 0
        buffer.clear()
    gc.collect()
