[Setup]
AppName=VTable
AppVersion=1.0
OutputBaseFilename=VTable-setup
DefaultDirName={pf}\VTable
DisableProgramGroupPage=yes
UninstallDisplayIcon={app}\VTable.exe
OutputDir=..\dist

[Tasks]
Name: "autostart"; Description: "Start on session startup"; Flags: unchecked

[Files]
Source: "..\dist\VTable\*"; DestDir: "{app}"; Flags: recursesubdirs

[Icons]
Name: "{commonprograms}\VTable"; Filename: "{app}\VTable.exe"
Name: "{commondesktop}\VTable"; Filename: "{app}\VTable.exe"
Name: "{userstartup}\VTable"; Filename: "{app}\VTable.exe"; Tasks: autostart
