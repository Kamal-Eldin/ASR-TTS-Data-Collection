#define ProgramName "Speech-Collector"
#define DockerSrcDir "docker_installer"
#define DockerExecutable "docker_windows.exe"

[Setup]
AppName={#ProgramName}
AppVersion=0.1
DefaultDirName={autopf64}\{#ProgramName}
DefaultGroupName= {#ProgramName}
OutputBaseFilename={#ProgramName}-Installer
Compression=lzma2/ultra64
WizardStyle=modern
PrivilegesRequired=admin
AllowRootDirectory=yes
AllowCancelDuringInstall=yes
CreateAppDir=yes
Uninstallable=yes
UninstallDisplayName={#ProgramName}
ArchitecturesAllowed=x86 x64 arm64
ArchitecturesInstallIn64BitMode= x64 arm64
; ExtraDiskSpaceRequired=1_073_741_824

[Languages]
Name: "en"; MessagesFile: "compiler:Default.isl"
; LicenseFile=license.txt
; InfoAfterFile=usage_instructions.txt

[Types]
Name: full    ; Description: "Full"
Name: compact ; Description: "Compact"

[Components]
Name: "main"; Description: "Application Files"; Types: full compact; Flags: fixed
Name: "docker"; Description: "Docker Desktop"; Types: full; Flags: exclusive

[Files]
Source: "https://desktop.docker.com/win/main/arm64/Docker%20Desktop%20Installer.exe"; DestDir: {app}\{#DockerSrcDir}; DestName: {#DockerExecutable}; ExternalSize: 550_000_000; Flags: external download ignoreversion

[Run]
Filename: "{app}\{#DockerSrcDir}\{#DockerExecutable}"; Parameters: "install --quiet"; Flags: 64bit
StatusMsg: "Installing Docker Desktop for Windows...Please wait..."






