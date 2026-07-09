#define MyAppName "Weebarr"
#define MyAppPublisher "DeepDaddyTTV"
#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif
#ifndef SourceDir
  #define SourceDir "."
#endif
#ifndef OutputDir
  #define OutputDir "."
#endif

[Setup]
AppId={{4A3F7784-1A88-4E17-885E-CC4C4C58D796}
AppName={#MyAppName}
AppVersion={#AppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\Weebarr
DefaultGroupName=Weebarr
OutputDir={#OutputDir}
OutputBaseFilename=Weebarr-{#AppVersion}-Windows-x64-Setup
Compression=lzma
SolidCompression=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest
WizardStyle=modern
UninstallDisplayIcon={app}\Weebarr.exe

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional icons:"

[Files]
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{autoprograms}\Weebarr"; Filename: "{app}\Weebarr.exe"
Name: "{autoprograms}\Stop Weebarr"; Filename: "{app}\Weebarr.exe"; Parameters: "--stop"
Name: "{autodesktop}\Weebarr"; Filename: "{app}\Weebarr.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\Weebarr.exe"; Description: "Launch Weebarr"; Flags: nowait postinstall skipifsilent
