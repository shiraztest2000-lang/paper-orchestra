#define AppName "SHZ PaperOrchestra"
#define AppVersion "0.1.0"
[Setup]
AppId={{EAB14C16-9A73-4E39-9B2D-4B7B8B0E45A1}
AppName={#AppName}
AppVersion={#AppVersion}
DefaultDirName={autopf}\SHZ PaperOrchestra
DefaultGroupName={#AppName}
OutputDir=..\dist-installer
OutputBaseFilename=SHZ-PaperOrchestra-Setup-{#AppVersion}-x64
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
[Files]
Source: "..\dist\SHZPaperOrchestra\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\SHZPaperOrchestra.exe"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\SHZPaperOrchestra.exe"; Tasks: desktopicon
[Tasks]
Name: "desktopicon"; Description: "Create desktop shortcut"; GroupDescription: "Additional icons:"
[Run]
Filename: "{app}\SHZPaperOrchestra.exe"; Description: "Launch {#AppName}"; Flags: postinstall nowait skipifsilent
