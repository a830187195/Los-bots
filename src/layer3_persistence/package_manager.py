"""Gestor de paquetes modulares (.mtjpack), hashes SHA-256 y actualizaciones Delta."""

from __future__ import annotations

import hashlib
import io
import json
import shutil
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.config.settings import APP_PATHS
from src.domain.models import OfflinePackageManifest, WorkflowFSM
from src.layer2_edge_ai.fsm_engine import WorkflowFSMEngine


@dataclass(frozen=True)
class DeltaPlan:
    """Plan diferencial para descargar únicamente archivos modificados (ahorro hasta ~90%)."""

    pack_id: str
    from_version: str
    to_version: str
    files_to_download: tuple[str, ...]
    files_to_delete: tuple[str, ...]
    unchanged_files: tuple[str, ...]
    savings_ratio: float


class OfflinePackageManager:
    """Empaqueta, instala, verifica integridad SHA-256 y aplica parches Delta."""

    def __init__(
        self,
        bundled_packs_dir: Path | None = None,
        installed_packs_dir: Path | None = None,
    ) -> None:
        self._bundled_dir = bundled_packs_dir or APP_PATHS.packs_dir
        self._installed_dir = installed_packs_dir or (
            APP_PATHS.root_dir / ".local_data" / "installed_packs"
        )
        self._installed_dir.mkdir(parents=True, exist_ok=True)

    def list_available_catalog(self) -> list[dict[str, Any]]:
        """Lista todos los paquetes disponibles en catálogo local y su estado de instalación."""
        catalog: list[dict[str, Any]] = []
        if not self._bundled_dir.exists():
            return catalog

        for pack_dir in sorted(self._bundled_dir.iterdir()):
            if not pack_dir.is_dir():
                continue
            wf_file = pack_dir / "workflow.json"
            if not wf_file.exists():
                continue
            raw = json.loads(wf_file.read_text(encoding="utf-8"))
            pack_id = raw["pack_id"]
            installed = self.is_installed(pack_id)
            manifest = self.build_manifest_from_dir(pack_dir, raw)
            catalog.append(
                {
                    "pack_id": pack_id,
                    "title": raw["title"],
                    "category": raw.get("category", "General"),
                    "version": raw.get("version", "1.0.0"),
                    "estimated_time": raw.get("estimated_time", ""),
                    "cost_summary": raw.get("cost_summary", ""),
                    "total_kb": max(1, round(manifest.total_bytes / 1024.0, 1)),
                    "installed": installed,
                    "steps_count": len(raw.get("states", [])),
                }
            )
        return catalog

    def is_installed(self, pack_id: str) -> bool:
        """Indica si el paquete ya está descargado, verificado y listo para Modo Avión."""
        return (self._installed_dir / pack_id / "workflow.json").exists()

    def install_from_bundled(self, pack_id: str) -> OfflinePackageManifest:
        """Empaqueta en .mtjpack, verifica SHA-256 e instala localmente un trámite."""
        source_dir = self._bundled_dir / pack_id
        if not (source_dir / "workflow.json").exists():
            raise FileNotFoundError(f"No existe el paquete fuente: {pack_id}")

        archive_bytes = self.export_mtjpack_bytes(source_dir)
        return self.install_mtjpack_bytes(archive_bytes)

    def uninstall_pack(self, pack_id: str) -> None:
        """Elimina un paquete descargado para liberar almacenamiento en el dispositivo."""
        target = self._installed_dir / pack_id
        if target.exists():
            shutil.rmtree(target)

    def load_workflow(self, pack_id: str) -> WorkflowFSM:
        """Carga el workflow.json priorizando la copia instalada verificada."""
        installed_wf = self._installed_dir / pack_id / "workflow.json"
        if installed_wf.exists():
            data = json.loads(installed_wf.read_text(encoding="utf-8"))
            return WorkflowFSMEngine.from_dict(data)

        bundled_wf = self._bundled_dir / pack_id / "workflow.json"
        if bundled_wf.exists():
            data = json.loads(bundled_wf.read_text(encoding="utf-8"))
            return WorkflowFSMEngine.from_dict(data)

        raise FileNotFoundError(f"Trámite no encontrado: {pack_id}")

    def get_installed_manifest(self, pack_id: str) -> OfflinePackageManifest | None:
        """Lee el manifiesto verificado de un paquete instalado."""
        manifest_path = self._installed_dir / pack_id / "manifest.json"
        if not manifest_path.exists():
            return None
        raw = json.loads(manifest_path.read_text(encoding="utf-8"))
        return OfflinePackageManifest(
            pack_id=raw["pack_id"],
            title=raw["title"],
            version=raw["version"],
            description=raw.get("description", ""),
            total_bytes=int(raw["total_bytes"]),
            file_hashes=dict(raw["file_hashes"]),
            languages_included=tuple(raw.get("languages_included", ["es"])),
            signature_hmac=raw.get("signature_hmac", ""),
        )

    def build_manifest_from_dir(
        self, pack_dir: Path, workflow_raw: dict[str, Any] | None = None
    ) -> OfflinePackageManifest:
        """Calcula hashes SHA-256 para todos los archivos del paquete."""
        if workflow_raw is None:
            workflow_raw = json.loads(
                (pack_dir / "workflow.json").read_text(encoding="utf-8")
            )
        file_hashes: dict[str, str] = {}
        total_bytes = 0
        for file_path in sorted(pack_dir.rglob("*")):
            if not file_path.is_file() or file_path.name == "manifest.json":
                continue
            rel = file_path.relative_to(pack_dir).as_posix()
            raw_bytes = file_path.read_bytes()
            total_bytes += len(raw_bytes)
            file_hashes[rel] = hashlib.sha256(raw_bytes).hexdigest()

        return OfflinePackageManifest(
            pack_id=workflow_raw["pack_id"],
            title=workflow_raw["title"],
            version=workflow_raw.get("version", "1.0.0"),
            description=workflow_raw.get("cost_summary", ""),
            total_bytes=total_bytes,
            file_hashes=file_hashes,
            languages_included=("es", "nah_puebla", "tot_sierra"),
        )

    def export_mtjpack_bytes(self, source_dir: Path) -> bytes:
        """Empaqueta un trámite en formato binario .mtjpack (ZIP + manifiesto SHA-256)."""
        manifest = self.build_manifest_from_dir(source_dir)
        manifest_dict = {
            "pack_id": manifest.pack_id,
            "title": manifest.title,
            "version": manifest.version,
            "description": manifest.description,
            "total_bytes": manifest.total_bytes,
            "file_hashes": manifest.file_hashes,
            "languages_included": list(manifest.languages_included),
        }

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(
                "manifest.json",
                json.dumps(manifest_dict, ensure_ascii=False, indent=2),
            )
            for rel_path in sorted(manifest.file_hashes.keys()):
                zf.write(source_dir / rel_path, arcname=rel_path)
        return buf.getvalue()

    def install_mtjpack_bytes(self, archive_bytes: bytes) -> OfflinePackageManifest:
        """Verifica hashes SHA-256 antes de extraer e instalar un paquete .mtjpack."""
        with zipfile.ZipFile(io.BytesIO(archive_bytes), "r") as zf:
            manifest_raw = json.loads(zf.read("manifest.json").decode("utf-8"))
            file_hashes: dict[str, str] = manifest_raw["file_hashes"]

            # Validación estricta de integridad y prevención de Zip Slip
            verified_files: dict[str, bytes] = {}
            for rel_path, expected_sha in file_hashes.items():
                if ".." in Path(rel_path).parts or rel_path.startswith("/"):
                    raise ValueError(f"Ruta insegura dentro de .mtjpack: {rel_path}")
                content = zf.read(rel_path)
                actual_sha = hashlib.sha256(content).hexdigest()
                if actual_sha != expected_sha:
                    raise ValueError(
                        f"Hash SHA-256 inválido para {rel_path} en paquete {manifest_raw['pack_id']}"
                    )
                verified_files[rel_path] = content

            pack_id = manifest_raw["pack_id"]
            dest_dir = self._installed_dir / pack_id
            if dest_dir.exists():
                shutil.rmtree(dest_dir)
            dest_dir.mkdir(parents=True, exist_ok=True)

            (dest_dir / "manifest.json").write_text(
                json.dumps(manifest_raw, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            for rel_path, content in verified_files.items():
                target = dest_dir / rel_path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(content)

        return OfflinePackageManifest(
            pack_id=manifest_raw["pack_id"],
            title=manifest_raw["title"],
            version=manifest_raw["version"],
            description=manifest_raw.get("description", ""),
            total_bytes=int(manifest_raw["total_bytes"]),
            file_hashes=file_hashes,
            languages_included=tuple(manifest_raw.get("languages_included", ["es"])),
        )

    @staticmethod
    def compute_delta_plan(
        local_manifest: OfflinePackageManifest | None,
        remote_manifest: OfflinePackageManifest,
    ) -> DeltaPlan:
        """Calcula únicamente las diferencias entre la versión local y la remota."""
        if local_manifest is None:
            all_files = tuple(sorted(remote_manifest.file_hashes.keys()))
            return DeltaPlan(
                pack_id=remote_manifest.pack_id,
                from_version="0.0.0",
                to_version=remote_manifest.version,
                files_to_download=all_files,
                files_to_delete=(),
                unchanged_files=(),
                savings_ratio=0.0,
            )

        local_hashes = local_manifest.file_hashes
        remote_hashes = remote_manifest.file_hashes

        to_download = tuple(
            sorted(
                rel
                for rel, h in remote_hashes.items()
                if local_hashes.get(rel) != h
            )
        )
        to_delete = tuple(
            sorted(rel for rel in local_hashes if rel not in remote_hashes)
        )
        unchanged = tuple(
            sorted(
                rel
                for rel, h in remote_hashes.items()
                if local_hashes.get(rel) == h
            )
        )
        total = max(1, len(remote_hashes))
        savings = round(len(unchanged) / float(total), 2)
        return DeltaPlan(
            pack_id=remote_manifest.pack_id,
            from_version=local_manifest.version,
            to_version=remote_manifest.version,
            files_to_download=to_download,
            files_to_delete=to_delete,
            unchanged_files=unchanged,
            savings_ratio=savings,
        )

    def apply_delta_patch(
        self,
        pack_id: str,
        patch_files: dict[str, bytes],
        target_manifest: OfflinePackageManifest,
    ) -> OfflinePackageManifest:
        """Aplica un parche diferencial verificando SHA-256 sin re-descargar activos intactos."""
        pack_dir = self._installed_dir / pack_id
        pack_dir.mkdir(parents=True, exist_ok=True)
        local_manifest = self.get_installed_manifest(pack_id)
        plan = self.compute_delta_plan(local_manifest, target_manifest)

        for rel in plan.files_to_delete:
            target = pack_dir / rel
            if target.exists():
                target.unlink()

        for rel in plan.files_to_download:
            if rel not in patch_files:
                raise ValueError(f"Falta archivo diferencial requerido: {rel}")
            data = patch_files[rel]
            actual_sha = hashlib.sha256(data).hexdigest()
            expected_sha = target_manifest.file_hashes[rel]
            if actual_sha != expected_sha:
                raise ValueError(f"Error de integridad SHA-256 en parche: {rel}")
            dest = pack_dir / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)

        manifest_dict = {
            "pack_id": target_manifest.pack_id,
            "title": target_manifest.title,
            "version": target_manifest.version,
            "description": target_manifest.description,
            "total_bytes": target_manifest.total_bytes,
            "file_hashes": target_manifest.file_hashes,
            "languages_included": list(target_manifest.languages_included),
        }
        (pack_dir / "manifest.json").write_text(
            json.dumps(manifest_dict, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return target_manifest
