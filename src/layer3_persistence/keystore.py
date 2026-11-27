"""Almacén de llaves criptográficas (Android Keystore vía pyjnius + respaldo local)."""

from __future__ import annotations

import os
import secrets
from pathlib import Path

from src.domain.interfaces import KeyStorePort


class AndroidKeyStoreProvider(KeyStorePort):
    """Gestiona la llave maestra de 256 bits sin incrustar secretos en el código fuente."""

    def __init__(self, storage_dir: Path) -> None:
        self._storage_dir = storage_dir
        self._storage_dir.mkdir(parents=True, exist_ok=True)
        self._key_file = self._storage_dir / ".mtj_keystore.bin"
        self._backend_name = "local_private_keystore"

    @property
    def backend_name(self) -> str:
        """Indica si la llave está protegida por Android Keystore hardware o archivo privado."""
        return self._backend_name

    def get_or_create_master_key(self, alias: str = "mtj_master_aes256") -> bytes:
        """Obtiene o genera de forma persistente una llave maestra AES-256 (32 bytes)."""
        android_key = self._try_android_keystore_wrap(alias)
        if android_key is not None:
            return android_key

        if self._key_file.exists():
            raw = self._key_file.read_bytes()
            if len(raw) == 32:
                return raw

        new_key = secrets.token_bytes(32)
        self._key_file.write_bytes(new_key)
        try:
            os.chmod(self._key_file, 0o600)
        except Exception:
            pass
        return new_key

    def _try_android_keystore_wrap(self, alias: str) -> bytes | None:
        """Intenta proteger la llave en AndroidKeyStore usando pyjnius cuando corre en APK."""
        try:
            from jnius import autoclass  # type: ignore import-not-found

            KeyStore = autoclass("java.security.KeyStore")
            KeyGenerator = autoclass("javax.crypto.KeyGenerator")
            KeyGenParameterSpecBuilder = autoclass(
                "android.security.keystore.KeyGenParameterSpec$Builder"
            )
            KeyProperties = autoclass("android.security.keystore.KeyProperties")

            ks = KeyStore.getInstance("AndroidKeyStore")
            ks.load(None)
            if not ks.containsAlias(alias):
                purposes = (
                    KeyProperties.PURPOSE_ENCRYPT | KeyProperties.PURPOSE_DECRYPT
                )
                spec = (
                    KeyGenParameterSpecBuilder(alias, purposes)
                    .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
                    .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
                    .setKeySize(256)
                    .build()
                )
                kg = KeyGenerator.getInstance(
                    KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore"
                )
                kg.init(spec)
                kg.generateKey()

            secret_key = ks.getKey(alias, None)
            Cipher = autoclass("javax.crypto.Cipher")
            GCMParameterSpec = autoclass("javax.crypto.spec.GCMParameterSpec")

            wrapped_path = self._storage_dir / ".mtj_keystore_wrapped.bin"
            if wrapped_path.exists():
                blob = wrapped_path.read_bytes()
                if len(blob) > 12:
                    iv, ct = blob[:12], blob[12:]
                    cipher = Cipher.getInstance("AES/GCM/NoPadding")
                    cipher.init(
                        Cipher.DECRYPT_MODE, secret_key, GCMParameterSpec(128, iv)
                    )
                    plain = bytes(cipher.doFinal(ct))
                    if len(plain) == 32:
                        self._backend_name = "android_keystore_hardware"
                        return plain

            master_key = secrets.token_bytes(32)
            cipher = Cipher.getInstance("AES/GCM/NoPadding")
            cipher.init(Cipher.ENCRYPT_MODE, secret_key)
            iv = bytes(cipher.getIV())
            ct = bytes(cipher.doFinal(master_key))
            wrapped_path.write_bytes(iv + ct)
            self._backend_name = "android_keystore_hardware"
            return master_key
        except Exception:
            return None
