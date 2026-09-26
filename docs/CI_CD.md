# CI/CD and Release Pipeline

## Workflow

The workflow is `.github/workflows/build.yml`.

It runs on pushes to `main` and can also be started manually.

## Stage 1 — Test

Windows runner:

1. checkout repository;
2. install Python 3.11;
3. install `requirements.txt`;
4. run `python -m pytest -q`;
5. verify `desktop` and `app.main` imports.

The desktop import check is important because packaging can fail on UI/import syntax even when API tests pass.

## Stage 2 — Build

The build job waits for the test job.

It:

1. checks out the repository;
2. installs Python 3.11 and dependencies;
3. installs PyInstaller;
4. validates packaging inputs;
5. determines whether SignPath configuration is present;
6. builds the executable;
7. optionally submits the executable for signing;
8. smoke-tests the packaged executable;
9. builds the Inno Setup installer;
10. optionally signs the installer;
11. generates SHA-256 checksums;
12. uploads executable, installer, and checksum artifacts.

## Signing branch

Signing is conditional on the required SignPath secrets/variables being configured.

Development/testing builds can remain unsigned. Release tags are configured to fail when signing is not configured.

## Artifact contract

The expected artifact names are:

- Windows executable;
- Windows installer;
- SHA-256 checksums.

## Why the pipeline has both tests and smoke test

Unit/API tests execute Python source directly. They cannot prove that the PyInstaller-produced executable starts successfully on Windows.

The smoke test closes that gap by launching the actual packaged executable.

## CI troubleshooting order

When CI fails, debug in this order:

1. syntax/import errors;
2. dependency installation;
3. pytest failures;
4. desktop import verification;
5. PyInstaller build;
6. packaged executable startup;
7. signing;
8. Inno Setup;
9. installer execution on a clean target.

Do not diagnose an installer problem as an ML/model problem unless the installer itself successfully launches and the failure occurs after runtime initialization.
