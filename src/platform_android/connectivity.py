"""Monitor no bloqueante de estado de conectividad (Android ConnectivityManager + simulación)."""

from __future__ import annotations

import socket
import sys
import time

from src.domain.interfaces import ConnectivityPort
from src.domain.models import NetworkStatus


class PlatformConnectivityMonitor(ConnectivityPort):
    """Detecta enlace de red sin congelar la interfaz y permite simular Modo Avión."""

    def __init__(self, force_offline: bool = False, cache_ttl_seconds: float = 5.0) -> None:
        self.force_offline = force_offline
        self._cache_ttl = cache_ttl_seconds
        self._last_checked: float = 0.0
        self._cached_status: NetworkStatus = NetworkStatus.OFFLINE

    def set_force_offline(self, offline: bool) -> None:
        """Activa o desactiva la simulación manual de Modo Sin Conexión."""
        self.force_offline = offline

    def get_network_status(self) -> NetworkStatus:
        """Retorna el estado de conectividad actual de forma rápida y no bloqueante."""
        if self.force_offline:
            return NetworkStatus.OFFLINE

        now = time.monotonic()
        if (now - self._last_checked) < self._cache_ttl:
            return self._cached_status

        status = self._probe_android()
        if status is None:
            status = self._probe_desktop_quick()

        self._cached_status = status
        self._last_checked = now
        return status

    @staticmethod
    def _probe_android() -> NetworkStatus | None:
        if "android" not in sys.platform and not _is_android_env():
            return None
        try:
            from jnius import autoclass  # type: ignore import-not-found

            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            Context = autoclass("android.content.Context")
            NetworkCapabilities = autoclass("android.net.NetworkCapabilities")

            activity = PythonActivity.mActivity
            cm = activity.getSystemService(Context.CONNECTIVITY_SERVICE)
            active_net = cm.getActiveNetwork()
            if active_net is None:
                return NetworkStatus.OFFLINE
            caps = cm.getNetworkCapabilities(active_net)
            if caps is None:
                return NetworkStatus.OFFLINE
            if caps.hasTransport(NetworkCapabilities.TRANSPORT_WIFI):
                return NetworkStatus.ONLINE_WIFI
            if caps.hasTransport(NetworkCapabilities.TRANSPORT_CELLULAR):
                return NetworkStatus.ONLINE_CELLULAR
            return NetworkStatus.OFFLINE
        except Exception:
            return None

    @staticmethod
    def _probe_desktop_quick() -> NetworkStatus:
        try:
            with socket.create_connection(("1.1.1.1", 53), timeout=0.35):
                return NetworkStatus.ONLINE_WIFI
        except OSError:
            return NetworkStatus.OFFLINE


def _is_android_env() -> bool:
    import os

    return "ANDROID_ARGUMENT" in os.environ or "ANDROID_PRIVATE" in os.environ
