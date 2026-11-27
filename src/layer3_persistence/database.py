"""Base de datos embebida SQLite con cifrado AES-256-GCM (y SQLCipher cuando está disponible)."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import sqlite3
from pathlib import Path

from src.domain.models import ProcedureProgress, SyncOperation, SyncStatus


class AES256Cipher:
    """Cifrado autenticado AES-256-GCM para proteger datos en reposo."""

    def __init__(self, master_key: bytes) -> None:
        if len(master_key) != 32:
            raise ValueError("La llave maestra debe ser exactamente de 32 bytes (256 bits).")
        self._key = master_key
        self._backend = self._detect_backend()

    @property
    def backend_name(self) -> str:
        """Devuelve el proveedor criptográfico activo."""
        return self._backend

    @staticmethod
    def _detect_backend() -> str:
        try:
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM  # type: ignore import-not-found

            _ = AESGCM
            return "aes_256_gcm_cryptography"
        except ImportError:
            pass
        try:
            from Crypto.Cipher import AES  # type: ignore import-not-found

            _ = AES
            return "aes_256_gcm_pycryptodome"
        except ImportError:
            return "hmac_sha256_authenticated_fallback"

    def encrypt_text(self, plaintext: str) -> str:
        """Cifra una cadena UTF-8 y la codifica en Base64 con nonce aleatorio."""
        data = plaintext.encode("utf-8")
        nonce = os.urandom(12)

        if self._backend == "aes_256_gcm_cryptography":
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM  # type: ignore import-not-found

            ct = AESGCM(self._key).encrypt(nonce, data, None)
            return base64.b64encode(b"G1" + nonce + ct).decode("ascii")

        if self._backend == "aes_256_gcm_pycryptodome":
            from Crypto.Cipher import AES  # type: ignore import-not-found

            cipher = AES.new(self._key, AES.MODE_GCM, nonce=nonce)
            ct, tag = cipher.encrypt_and_digest(data)
            return base64.b64encode(b"G1" + nonce + ct + tag).decode("ascii")

        # Respaldo puro en stdlib (HMAC-SHA256 CTR + etiqueta de autenticación)
        stream = _derive_keystream(self._key, nonce, len(data))
        ct = bytes(a ^ b for a, b in zip(data, stream))
        tag = hmac.new(self._key, nonce + ct, hashlib.sha256).digest()
        return base64.b64encode(b"H1" + nonce + ct + tag).decode("ascii")

    def decrypt_text(self, token_b64: str) -> str:
        """Verifica autenticidad y descifra el token almacenado."""
        blob = base64.b64decode(token_b64.encode("ascii"))
        header = blob[:2]
        nonce = blob[2:14]
        body = blob[14:]

        if header == b"G1":
            if self._backend == "aes_256_gcm_cryptography":
                from cryptography.hazmat.primitives.ciphers.aead import AESGCM  # type: ignore import-not-found

                plain = AESGCM(self._key).decrypt(nonce, body, None)
                return plain.decode("utf-8")
            if self._backend == "aes_256_gcm_pycryptodome":
                from Crypto.Cipher import AES  # type: ignore import-not-found

                ct, tag = body[:-16], body[-16:]
                cipher = AES.new(self._key, AES.MODE_GCM, nonce=nonce)
                plain = cipher.decrypt_and_verify(ct, tag)
                return plain.decode("utf-8")

        if header == b"H1":
            ct, tag = body[:-32], body[-32:]
            expected = hmac.new(self._key, nonce + ct, hashlib.sha256).digest()
            if not hmac.compare_digest(tag, expected):
                raise ValueError("Integridad comprometida al descifrar registro local.")
            stream = _derive_keystream(self._key, nonce, len(ct))
            plain = bytes(a ^ b for a, b in zip(ct, stream))
            return plain.decode("utf-8")

        raise ValueError("Formato de cifrado desconocido o librería incompatible.")


def _derive_keystream(key: bytes, nonce: bytes, length: int) -> bytes:
    blocks = bytearray()
    counter = 0
    while len(blocks) < length:
        block = hmac.new(
            key, nonce + counter.to_bytes(4, "big"), hashlib.sha256
        ).digest()
        blocks.extend(block)
        counter += 1
    return bytes(blocks[:length])


class EncryptedSQLiteRepository:
    """Repositorio SQLite/SQLCipher cifrado para progreso FSM, caché y cola de sincronización."""

    def __init__(self, db_path: Path, master_key: bytes) -> None:
        self._db_path = db_path
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._cipher = AES256Cipher(master_key)
        self._sqlcipher_active = False
        self._conn = self._open_connection(master_key)
        self._init_schema()

    @property
    def security_summary(self) -> str:
        """Resumen legible del nivel de cifrado activo en almacenamiento."""
        engine = "SQLCipher" if self._sqlcipher_active else "SQLite-WAL"
        return f"{engine} + {self._cipher.backend_name}"

    def _open_connection(self, master_key: bytes) -> sqlite3.Connection:
        try:
            import sqlcipher3  # type: ignore import-not-found

            conn = sqlcipher3.connect(str(self._db_path), check_same_thread=False)
            hex_key = master_key.hex()
            conn.execute(f"PRAGMA key = \"x'{hex_key}'\";")
            self._sqlcipher_active = True
            return conn
        except ImportError:
            conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA synchronous=NORMAL;")
            return conn

    def _init_schema(self) -> None:
        with self._conn:
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS procedure_progress (
                    pack_id TEXT PRIMARY KEY,
                    encrypted_payload TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                """
            )
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS preferences (
                    pref_key TEXT PRIMARY KEY,
                    encrypted_value TEXT NOT NULL
                );
                """
            )
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS translation_cache (
                    cache_key TEXT PRIMARY KEY,
                    encrypted_payload TEXT NOT NULL
                );
                """
            )
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS sync_queue (
                    op_id TEXT PRIMARY KEY,
                    op_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    attempt_count INTEGER NOT NULL,
                    next_retry_epoch REAL NOT NULL,
                    encrypted_payload TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    last_error TEXT NOT NULL
                );
                """
            )

    def save_progress(self, progress: ProcedureProgress) -> None:
        """Guarda de manera atómica el estado FSM del usuario cifrado con AES-256."""
        payload = json.dumps(
            {
                "pack_id": progress.pack_id,
                "current_state_id": progress.current_state_id,
                "completed_checklist": progress.completed_checklist,
                "selected_office": progress.selected_office,
                "payment_exempt": progress.payment_exempt,
                "updated_at_iso": progress.updated_at_iso,
            },
            ensure_ascii=False,
        )
        token = self._cipher.encrypt_text(payload)
        with self._conn:
            self._conn.execute(
                """
                INSERT INTO procedure_progress (pack_id, encrypted_payload, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(pack_id) DO UPDATE SET
                    encrypted_payload = excluded.encrypted_payload,
                    updated_at = excluded.updated_at;
                """,
                (progress.pack_id, token, progress.updated_at_iso),
            )

    def load_progress(self, pack_id: str) -> ProcedureProgress | None:
        """Carga y descifra el estado guardado de un trámite."""
        cur = self._conn.execute(
            "SELECT encrypted_payload FROM procedure_progress WHERE pack_id = ?;",
            (pack_id,),
        )
        row = cur.fetchone()
        if row is None:
            return None
        raw = json.loads(self._cipher.decrypt_text(row[0]))
        return ProcedureProgress(
            pack_id=raw["pack_id"],
            current_state_id=raw["current_state_id"],
            completed_checklist=raw.get("completed_checklist", {}),
            selected_office=raw.get("selected_office", ""),
            payment_exempt=bool(raw.get("payment_exempt", False)),
            updated_at_iso=raw.get("updated_at_iso", ""),
        )

    def save_preference(self, key: str, value: str) -> None:
        """Guarda una preferencia del ciudadano cifrada."""
        token = self._cipher.encrypt_text(value)
        with self._conn:
            self._conn.execute(
                """
                INSERT INTO preferences (pref_key, encrypted_value)
                VALUES (?, ?)
                ON CONFLICT(pref_key) DO UPDATE SET
                    encrypted_value = excluded.encrypted_value;
                """,
                (key, token),
            )

    def load_preference(self, key: str, default: str = "") -> str:
        """Lee una preferencia local cifrada."""
        cur = self._conn.execute(
            "SELECT encrypted_value FROM preferences WHERE pref_key = ?;",
            (key,),
        )
        row = cur.fetchone()
        if row is None:
            return default
        try:
            return self._cipher.decrypt_text(row[0])
        except Exception:
            return default

    def enqueue_sync(self, operation: SyncOperation) -> None:
        """Inserta o actualiza una operación asíncrona en la cola persistente."""
        payload_json = json.dumps(operation.payload, ensure_ascii=False)
        token = self._cipher.encrypt_text(payload_json)
        with self._conn:
            self._conn.execute(
                """
                INSERT INTO sync_queue (
                    op_id, op_type, status, attempt_count, next_retry_epoch,
                    encrypted_payload, created_at, last_error
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(op_id) DO UPDATE SET
                    status = excluded.status,
                    attempt_count = excluded.attempt_count,
                    next_retry_epoch = excluded.next_retry_epoch,
                    encrypted_payload = excluded.encrypted_payload,
                    last_error = excluded.last_error;
                """,
                (
                    operation.op_id,
                    operation.op_type,
                    operation.status.value,
                    operation.attempt_count,
                    operation.next_retry_epoch,
                    token,
                    operation.created_at_iso,
                    operation.last_error,
                ),
            )

    def list_due_sync_operations(self, now_epoch: float) -> list[SyncOperation]:
        """Obtiene operaciones pendientes listas para reintento según backoff."""
        cur = self._conn.execute(
            """
            SELECT op_id, op_type, status, attempt_count, next_retry_epoch,
                   encrypted_payload, created_at, last_error
            FROM sync_queue
            WHERE status IN (?, ?) AND next_retry_epoch <= ?
            ORDER BY next_retry_epoch ASC;
            """,
            (SyncStatus.PENDING.value, SyncStatus.RETRY_WAIT.value, now_epoch),
        )
        ops: list[SyncOperation] = []
        for row in cur.fetchall():
            payload = json.loads(self._cipher.decrypt_text(row[5]))
            ops.append(
                SyncOperation(
                    op_id=row[0],
                    op_type=row[1],
                    status=SyncStatus(row[2]),
                    attempt_count=int(row[3]),
                    next_retry_epoch=float(row[4]),
                    payload=payload,
                    created_at_iso=row[6],
                    last_error=row[7],
                )
            )
        return ops

    def count_pending_sync(self) -> int:
        """Cuenta cuántas operaciones siguen esperando conexión."""
        cur = self._conn.execute(
            "SELECT COUNT(*) FROM sync_queue WHERE status IN (?, ?);",
            (SyncStatus.PENDING.value, SyncStatus.RETRY_WAIT.value),
        )
        row = cur.fetchone()
        return int(row[0]) if row else 0

    def close(self) -> None:
        """Cierra la conexión SQLite de manera limpia."""
        self._conn.close()
