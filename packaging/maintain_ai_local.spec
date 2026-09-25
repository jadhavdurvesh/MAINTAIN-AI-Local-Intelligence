from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules

if "__file__" in globals():
    SPEC_DIR = Path(__file__).resolve().parent
else:
    SPEC_DIR = Path.cwd() / "packaging"

APP_ROOT = SPEC_DIR.parent
ENTRYPOINT = APP_ROOT / "desktop.py"

if not ENTRYPOINT.is_file():
    raise FileNotFoundError(f"Desktop entrypoint not found: {ENTRYPOINT}")

hidden = collect_submodules("app")

a = Analysis(
    [str(ENTRYPOINT)],
    pathex=[str(APP_ROOT)],
    binaries=[],
    datas=[],
    hiddenimports=hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["torch", "transformers", "chronos", "safetensors"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="MAINTAIN-AI-Local-Intelligence",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)
