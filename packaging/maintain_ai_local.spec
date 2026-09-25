from PyInstaller.utils.hooks import collect_submodules

# The spec file lives in packaging/, while the desktop entrypoint lives at
# the repository root. PyInstaller resolves Analysis paths relative to the
# spec file, so use the parent directory explicitly.
APP_ROOT = ".."
hidden = collect_submodules("app")

a = Analysis(
    ["../desktop.py"],
    pathex=[APP_ROOT],
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
