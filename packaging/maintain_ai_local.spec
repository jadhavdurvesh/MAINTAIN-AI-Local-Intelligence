from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules

# PyInstaller executes the spec file without defining __file__ in some
# versions. The GitHub Actions build runs from the repository root, so keep
# the fallback deterministic while still supporting direct local invocation.
if "__file__" in globals():
    SPEC_DIR = Path(__file__).resolve().parent
else:
    SPEC_DIR = Path.cwd() / "packaging"

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
