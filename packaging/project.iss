[Setup]
appName=ObjectViz
AppVersion={#GetEnv("VERSION")}
OutputBaseFilename=ObjectViz-setup
DefaultDirName={pf}\ObjectViz
DisableProgramGroupPage=yes
UninstallDisplayIcon={app}\ObjectViz.exe
OutputDir=..\dist

[Tasks]
Name: "autostart"; Description: "Start ObjectViz on session startup"; Flags: unchecked

[Files]
Source: "..\dist\ObjectViz\*"; DestDir: "{app}"; Flags: recursesubdirs

[Icons]
Name: "{commonprograms}\ObjectViz"; Filename: "{app}\ObjectViz.exe"
Name: "{commondesktop}\ObjectViz"; Filename: "{app}\ObjectViz.exe"
Name: "{userstartup}\ObjectViz"; Filename: "{app}\ObjectViz.exe"; Tasks: autostart
