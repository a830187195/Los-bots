"""Cola de sincronización persistente con política de reintentos exponenciales."""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone
from typing import Any, Callable

from src.domain.interfaces import ConnectivityPort
from src.domain.models import NetworkStatus, SyncOperation, SyncStatus
from src.layer3_persistence.database import EncryptedSQLiteRepository


class SmartSyncQueue:
    """Gestiona reconciliación diferida con la nube sin bloquear la experiencia offline."""

    def __init__(
        self,
        repository: EncryptedSQLiteRepository,
        connectivity: ConnectivityPort,
        base_delay_seconds: float = 5.0,
        max_delay_seconds: float = 3600.0,
        max_attempts: int = 6,
    ) -> None:
        self._repo = repository
        self._connectivity = connectivity
        self._base_delay = base_delay_seconds
        self._max_delay = max_delay_seconds
        self._max_attempts = max_attempts

    def enqueue(
        self, op_type: str, payload: dict[str, Any], now_epoch: float | None = None
    ) -> SyncOperation:
        """Agrega una operación anónima a la cola cifrada local."""
        now = time.time() if now_epoch is None else now_epoch
        op = SyncOperation(
            op_id=str(uuid.uuid4()),
            op_type=op_type,
            payload=payload,
            status=SyncStatus.PENDING,
            attempt_count=0,
            next_retry_epoch=now,
            created_at_iso=datetime.now(timezone.utc).isoformat(timespec="seconds"),
            last_error="",
        )
        self._repo.enqueue_sync(op)
        return op

    def calculate_backoff_seconds(self, attempt_number: int) -> float:
        """Calcula el tiempo de espera exponencial: base * 2^(intento-1)."""
        exponent = max(0, attempt_number - 1)
        return min(self._max_delay, self._base_delay * (2**exponent))

    def process_due(
        self,
        dispatcher: Callable[[SyncOperation], bool],
        now_epoch: float | None = None,
    ) -> dict[str, int]:
        """Intenta sincronizar tareas vencidas solo si hay conectividad activa."""
        status = self._connectivity.get_network_status()
        if status == NetworkStatus.OFFLINE:
            return {"processed": 0, "succeeded": 0, "rescheduled": 0, "skipped_offline": 1}

        now = time.time() if now_epoch is None else now_epoch
        due_ops = self._repo.list_due_sync_operations(now)
        succeeded = 0
        rescheduled = 0

        for op in due_ops:
            ok = False
            err_msg = ""
            try:
                ok = dispatcher(op)
            except Exception as exc:
                err_msg = str(exc)

            if ok:
                op.status = SyncStatus.COMPLETED
                op.last_error = ""
                succeeded += 1
            else:
                op.attempt_count += 1
                if op.attempt_count >= self._max_attempts:
                    op.status = SyncStatus.FAILED_PERMANENT
                else:
                    op.status = SyncStatus.RETRY_WAIT
                    delay = self.calculate_backoff_seconds(op.attempt_count)
                    op.next_retry_epoch = now + delay
                op.last_error = err_msg or "Red inestable o servicio no disponible"
                rescheduled += 1

            self._repo.enqueue_sync(op)

        return {
            "processed": len(due_ops),
            "succeeded": succeeded,
            "rescheduled": rescheduled,
            "skipped_offline": 0,
        }

    def pending_count(self) -> int:
        """Número de operaciones actualmente en espera."""
        return self._repo.count_pending_sync()
