# MAINTAIN AI Windows code signing

MAINTAIN AI produces two Windows executables:

- `MAINTAIN-AI-Local-Intelligence.exe`
- `MAINTAIN-AI-Local-Intelligence-Setup.exe`

The GitHub Actions workflow supports SignPath Authenticode signing for both files. The application is signed **before** Inno Setup packages it, and the installer is signed afterwards. This means the executable users install is signed as well as the installer they download.

## Why signing is separate from building

PyInstaller and Inno Setup can build valid Windows executables without a publisher certificate. Windows Smart App Control and reputation-based security can still block an unsigned or untrusted executable. Code signing establishes the publisher identity and integrity of the executable; it does not replace antivirus scanning or make unsafe code safe.

Do not disable Windows security just to distribute the MAINTAIN AI installer. Configure trusted code signing for release builds instead.

## SignPath setup

SignPath provides a GitHub Actions integration documented at:

- https://docs.signpath.io/trusted-build-systems/github
- https://github.com/SignPath/github-action-submit-signing-request

For an open-source project, apply for the SignPath open-source program if the repository meets their current eligibility requirements. If SignPath approves the project, create a SignPath project for MAINTAIN AI and configure a trusted signing certificate/policy there.

### Repository secret

In GitHub:

`Settings -> Secrets and variables -> Actions -> Secrets -> New repository secret`

Create:

`SIGNPATH_API_TOKEN`

Paste the API token generated in SignPath. Never commit this token to the repository.

### Repository variables

In:

`Settings -> Secrets and variables -> Actions -> Variables`

Create these repository variables using the exact slugs/IDs shown by your SignPath project:

- `SIGNPATH_ORGANIZATION_ID`
- `SIGNPATH_PROJECT_SLUG`
- `SIGNPATH_APP_POLICY_SLUG`
- `SIGNPATH_INSTALLER_POLICY_SLUG`
- `SIGNPATH_APP_ARTIFACT_CONFIG_SLUG`
- `SIGNPATH_INSTALLER_ARTIFACT_CONFIG_SLUG`

The workflow intentionally does not hard-code your private SignPath organization/project identifiers.

## Artifact configurations

Create an artifact configuration for the desktop executable that applies Authenticode signing to the PE file. Create a second artifact configuration for the Inno Setup installer.

The exact artifact configuration names/slugs depend on the SignPath project and certificate setup, so the workflow reads them from GitHub repository variables instead of inventing them.

## Workflow behavior

### Normal `main` pushes

If SignPath is not configured yet, the workflow continues and creates clearly named **unsigned** development artifacts. This keeps normal development builds usable while the signing account is being set up.

If SignPath is configured, the same workflow signs both the application and installer and verifies their Authenticode status before uploading the final artifacts.

### Release tags

Release tags require SignPath configuration. If the required signing values are missing, the release build fails rather than silently publishing an unsigned release installer.

## Release checklist

1. Apply for/activate the appropriate SignPath open-source signing program.
2. Create the MAINTAIN AI project in SignPath.
3. Configure the trusted release certificate and signing policies.
4. Create the application and installer artifact configurations.
5. Add `SIGNPATH_API_TOKEN` as a GitHub Actions repository secret.
6. Add the six SignPath repository variables listed above.
7. Push to `main` and confirm the workflow reports `SignPath signing is configured.`
8. Confirm both resulting files show a valid Authenticode signature.
9. Create a release tag only after the signed workflow succeeds.

## Local verification on Windows

PowerShell can inspect the signature with:

```powershell
Get-AuthenticodeSignature .\MAINTAIN-AI-Local-Intelligence.exe | Format-List *
Get-AuthenticodeSignature .\MAINTAIN-AI-Local-Intelligence-Setup.exe | Format-List *
```

The release workflow also performs this check automatically and fails if the signed artifact does not report `Valid`.

## Important limitation

Adding the GitHub Action to this repository does **not** itself create a trusted publisher identity. SignPath must issue/authorize the certificate and the repository owner must configure the SignPath organization/project credentials. Those credentials cannot safely be generated or committed by the source repository.
