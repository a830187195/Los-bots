# -*- mode: python ; coding: utf-8 -*-
"""Especificación PyInstaller para generar ejecutable standalone MiTramiteJusto.exe en Windows."""

from pathlib import Path

try:
    from kivy_deps import angle, glew, sdl2  # type: ignore import-not-found

    _KIVY_TREES = [Tree(p) for p in (sdl2.dep_bins + glew.dep_bins + angle.dep_bins)]
except Exception:
    _KIVY_TREES = []

block_cipher = None
ROOT = Path(".").resolve()

a = Analysis(
    ["main.py"],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[
        (str(ROOT / "assets"), "assets"),
        (str(ROOT / "src"), "src"),
    ],
    hiddenimports=[
        "kivy",
        "PIL",
        "cryptography",
        "plyer",
        "plyer.platforms.win.filechooser",
        "src.layer1_presentation.screens.translator_screen",
        "src.layer1_presentation.screens.scanner_screen",
        "src.layer1_presentation.screens.offline_hub_screen",
        "src.layer1_presentation.screens.guide_screen",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["pytest", "ruff", "mypy"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    *_KIVY_TREES,
    name="MiTramiteJusto",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    icon=str(ROOT / "assets" / "branding" / "logo.png"),
)
