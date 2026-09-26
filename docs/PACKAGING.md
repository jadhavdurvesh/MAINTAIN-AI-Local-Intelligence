# Windows Packaging

## Build products

The CI pipeline produces two primary Windows deliverables:

1. `MAINTAIN-AI-Local-Intelligence.exe` — packaged desktop executable.
2. `MAINTAIN-AI-Local-Intelligence-Setup.exe` — Windows installer.

A SHA-256 checksum file is also generated.

## PyInstaller

`packaging/maintain_ai_local.spec` defines the PyInstaller build.

CI invokes:

```text
pyinstaller packaging/maintain_ai_local.spec --noconfirm --clean --log-level WARN
```

The executable is checked for existence before continuing.

## Inno Setup

`packaging/installer.iss` builds the installer around the packaged application.

CI invokes the installed Inno Setup compiler on Windows and verifies the resulting installer exists.

## Code signing

The workflow supports optional SignPath signing for both the application and installer.

If signing configuration is absent, normal development builds may continue unsigned. Release tags require signing configuration according to the current workflow.

See `docs/SIGNING.md` for the detailed signing process.

## Heavy model boundary

The base installer should not silently bundle huge model checkpoints. Heavy model dependencies/checkpoints are intentionally optional and are managed separately.

This keeps the desktop installer practical for machines with limited RAM/storage and allows operators to install only the intelligence they need.

## Smoke test

After building the executable, CI starts it briefly. If it exits during startup, the packaging job fails.

This catches basic packaged-runtime failures that import tests alone cannot catch.

## Packaging failure classes

When troubleshooting a build, distinguish:

- Python/import failure;
- PyInstaller collection failure;
- packaged runtime startup failure;
- signing failure;
- Inno Setup failure;
- installer runtime failure on the target PC.

These occur at different stages and should be debugged separately.
