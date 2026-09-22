; Inno Setup script for PicPur
; Build with: iscc installer.iss
; Requires the onedir PyInstaller build to already exist in dist\PicPur

#define MyAppName "PicPur"
#define MyAppExeName "PicPur.exe"
#define MyAppPublisher "PicPur"

; Read the version straight from version.py (a single line: __version__ = "x.y.z") so the installer always matches the app.
#define FileHandle FileOpen(SourcePath + "version.py")
#define FileLine FileRead(FileHandle)
#expr FileClose(FileHandle)
#define MyAppVersion Copy(FileLine, Pos('"', FileLine) + 1, RPos('"', FileLine) - Pos('"', FileLine) - 1)

[Setup]
AppId={{9C6F6E8E-6C6B-4B62-9C1C-2E9A8C9F4F3A}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=installer_output
OutputBaseFilename=PicPur-Setup-{#MyAppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#MyAppExeName}
SetupIconFile=assets\icon.ico

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional icons:"; Flags: unchecked

[Files]
Source: "dist\PicPur\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent
