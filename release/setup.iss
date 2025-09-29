[Setup]
AppName=Speech Collector
AppVersion=0.1
DefaultDirName={autopf}\Speech Collector
DefaultGroupName= Collector
OutputBaseFilename=SpeechCollector-Installer
Compression=lzma2/ultra64
WizardStyle=modern
PrivilegesRequired=admin
AllowRootDirectory=yes
AllowCancelDuringInstall=yes
CreateAppDir=yes
Uninstallable=yes
; ExtraDiskSpaceRequired=1_073_741_824

[Languages]
Name: "en"; MessagesFile: "compiler:Default.isl"
; LicenseFile=license.txt
; InfoAfterFile=usage_instructions.txt

[Types]
Name: full    ; Description: "Full Installation"
Name: compact ; Description: "Main program without docker"

[Components]
Name: "main"; Description: "Main program Files"; Types: full compact; Flags: fixed
Name: "docker"; Description: "Docker standalone binaries"; Types: full

[Files]
Source: "https://desktop.docker.com/win/main/arm64/Docker%20Desktop%20Installer.exe"; DestDir: {app}; DestName: docker_windows.exe; ExternalSize: 550_000_000; Flags: external download ignoreversion







