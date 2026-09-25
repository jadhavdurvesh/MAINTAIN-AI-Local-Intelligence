#define MyAppName "MAINTAIN AI Local Intelligence"
#define MyAppVersion "0.6.3"
#define MyAppPublisher "MAINTAIN AI"
#define MyAppExeName "MAINTAIN-AI-Local-Intelligence.exe"

[Setup]
AppId={{B6E3F9D8-9B44-4D7A-8E15-1B1C6B7C6F20}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\MAINTAIN AI\Local Intelligence
DefaultGroupName={#MyAppName}
OutputDir=..\dist\installer
OutputBaseFilename=MAINTAIN-AI-Local-Intelligence-Setup
Compression=lzma2
SolidCompression=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64
WizardStyle=modern
PrivilegesRequired=admin
UninstallDisplayIcon={app}\{#MyAppExeName}

[Files]
Source: "..\dist\MAINTAIN-AI-Local-Intelligence.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\docs\INSTALL.md"; DestDir: "{app}\docs"; Flags: ignoreversion
Source: "..\docs\ARCHITECTURE.md"; DestDir: "{app}\docs"; Flags: ignoreversion
Source: "..\docs\INTEGRATION.md"; DestDir: "{app}\docs"; Flags: ignoreversion
Source: "..\docs\MODELS.md"; DestDir: "{app}\docs"; Flags: ignoreversion
Source: "..\docs\PROJECT_MAP.md"; DestDir: "{app}\docs"; Flags: ignoreversion
Source: "..\scripts\install_models.py"; DestDir: "{app}\scripts"; Flags: ignoreversion

[Dirs]
Name: "{userappdata}\MAINTAIN AI"
Name: "{userappdata}\MAINTAIN AI\Local Intelligence"

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent
