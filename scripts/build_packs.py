"""Script de empaquetado para generar archivos .mtjpack listos para CDN y verificar SHA-256."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config.settings import APP_PATHS
from src.layer3_persistence.package_manager import OfflinePackageManager


def main() -> None:
    """Construye y valida todos los paquetes .mtjpack en dist_packs/."""
    dist_dir = ROOT / "dist_packs"
    dist_dir.mkdir(parents=True, exist_ok=True)
    manager = OfflinePackageManager(
        bundled_packs_dir=APP_PATHS.packs_dir,
        installed_packs_dir=ROOT / ".local_data" / "verify_packs",
    )

    for pack_dir in sorted(APP_PATHS.packs_dir.iterdir()):
        if not pack_dir.is_dir() or not (pack_dir / "workflow.json").exists():
            continue
        archive_bytes = manager.export_mtjpack_bytes(pack_dir)
        manifest = manager.install_mtjpack_bytes(archive_bytes)
        out_file = dist_dir / f"{manifest.pack_id}-{manifest.version}.mtjpack"
        out_file.write_bytes(archive_bytes)
        print(
            f"[OK] {out_file.name}: {len(archive_bytes)} bytes, "
            f"{len(manifest.file_hashes)} archivos SHA-256 verificados."
        )


if __name__ == "__main__":
    main()
