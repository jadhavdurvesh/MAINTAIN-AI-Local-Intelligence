from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules

# Resolve paths from the spec file itself. GitHub Actions invokes PyInstaller
# from the repository root, so a relative "../desktop.py" is otherwise
# resolved against the wrong working directory on some PyInstaller versions.
SPEC_DIR = Path(__file__).resolve().parent
APP_ROOT = SPEC_DIR.parent
ENTRYPOINT = APP_ROOT / "desktop.py"

hidden = collect_submodules("app")

if not ENTRYPOINT.is_file():
    raise FileNotFoundError(f"Desktop entrypoint not found: {ENTRYPOINT}")

a = Analysis(
    [str(ENTRYPOINT)],
    pathex=[str(APP_ROOT)],
    binaries=[],
    datas=[],
    hiddenimports=hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
