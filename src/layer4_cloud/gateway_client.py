"""Cliente HTTPS/TLS 1.3 con Certificate Pinning y fallback transparente a modo Offline."""

from __future__ import annotations

import base64
import hashlib
import json
import ssl
import urllib.error
import urllib.request
from typing import Any
from urllib.parse import urlparse

from src.config.settings import SLA_TARGETS
from src.domain.interfaces import CloudGatewayPort
from src.domain.models import OfflinePackageManifest, TranslationResult
from src.layer4_cloud.contracts import NMTRequestDTO


class CertificatePinningError(ssl.SSLError):
    """Se lanza internamente si la huella SHA-256 del servidor no coincide con el pin."""


class SecureCloudGatewayClient(CloudGatewayPort):
    """Cliente hacia API Gateway Go/CDN que nunca bloquea ni propaga fallos de red al usuario."""

    def __init__(
        self,
        base_url: str,
        pinned_cert_sha256: str,
        timeout_seconds: float = SLA_TARGETS.cloud_request_timeout_seconds,
        enable_pinning: bool = True,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._pinned_sha256 = pinned_cert_sha256.strip()
        self._timeout = timeout_seconds
        self._enable_pinning = enable_pinning

    def translate_nmt(
        self, text: str, source_lang: str, target_lang: str
    ) -> TranslationResult | None:
        """Invoca microservicio NMT con TLS 1.3; devuelve None ante cualquier fallo de red."""
        dto = NMTRequestDTO(
            text=text, source_lang=source_lang, target_lang=target_lang
        )
        data = self._request_json(
            method="POST",
            path="/nmt/translate",
            payload=dto.to_safe_dict(),
        )
        if not data or "translated_text" not in data:
            return None

        return TranslationResult(
            source_text=text,
            translated_text=str(data["translated_text"]),
            phonetic_guide=str(data.get("phonetic_guide", "")),
            source_lang=source_lang,
            target_lang=target_lang,
            engine_used="cloud_nmt",
            confidence=float(data.get("confidence", 0.92)),
            citizen_note="Traducción generada con modelo neuronal en la nube.",
        )

    def fetch_remote_manifest(self, pack_id: str) -> OfflinePackageManifest | None:
        """Consulta en CDN la versión vigente y hashes SHA-256 para cálculo de deltas."""
        data = self._request_json(
            method="GET", path=f"/cdn/packs/{pack_id}/manifest.json"
        )
        if not data or "file_hashes" not in data:
            return None

        return OfflinePackageManifest(
            pack_id=str(data["pack_id"]),
            title=str(data["title"]),
            version=str(data["version"]),
            description=str(data.get("description", "")),
            total_bytes=int(data.get("total_bytes", 0)),
            file_hashes=dict(data["file_hashes"]),
            languages_included=tuple(data.get("languages_included", ["es"])),
            signature_hmac=str(data.get("signature_hmac", "")),
        )

    def dispatch_anonymous_sync(self, op_type: str, payload: dict[str, Any]) -> bool:
        """Envía operaciones diferidas anonimizadas; devuelve True si el Gateway confirmó."""
        res = self._request_json(
            method="POST",
            path=f"/sync/{op_type}",
            payload=payload,
        )
        return res is not None and bool(res.get("ok", True))

    def verify_certificate_der(self, cert_der: bytes) -> bool:
        """Comprueba si el certificado DER coincide con la huella SHA-256 anclada."""
        if not self._enable_pinning or not self._pinned_sha256:
            return True
        digest = hashlib.sha256(cert_der).digest()
        pin = "sha256/" + base64.b64encode(digest).decode("ascii")
        return pin == self._pinned_sha256

    def _build_tls13_context(self) -> ssl.SSLContext:
        ctx = ssl.create_default_context()
        if hasattr(ssl, "TLSVersion"):
            ctx.minimum_version = ssl.TLSVersion.TLSv1_3
        ctx.check_hostname = True
        ctx.verify_mode = ssl.CERT_REQUIRED
        return ctx

    def _request_json(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        url = f"{self._base_url}{path}"
        parsed = urlparse(url)
        if parsed.scheme != "https":
            return None

        try:
            ctx = self._build_tls13_context()
            if self._enable_pinning and parsed.hostname:
                port = parsed.port or 443
                with ctx.wrap_socket(
                    self._create_tcp_socket(parsed.hostname, port),
                    server_hostname=parsed.hostname,
                ) as tls_sock:
                    der = tls_sock.getpeercert(binary_form=True)
                    if not der or not self.verify_certificate_der(der):
                        raise CertificatePinningError("Certificate Pinning mismatch")

            body_bytes = (
                json.dumps(payload, ensure_ascii=False).encode("utf-8")
                if payload is not None
                else None
            )
            req = urllib.request.Request(
                url=url,
                data=body_bytes,
                method=method,
                headers={"Content-Type": "application/json", "Accept": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=self._timeout, context=ctx) as resp:
                if resp.status < 200 or resp.status >= 300:
                    return None
                raw = resp.read().decode("utf-8")
                return json.loads(raw) if raw else {"ok": True}
        except (urllib.error.URLError, ssl.SSLError, TimeoutError, OSError, ValueError):
            return None

    def _create_tcp_socket(self, host: str, port: int) -> Any:
        import socket

        return socket.create_connection((host, port), timeout=self._timeout)
