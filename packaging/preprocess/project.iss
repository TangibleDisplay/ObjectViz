[Setup]
AppName={{NAME}}
AppVersion={{VERSION}}
OutputBaseFilename={{NAME}}{{DEBUG}}-setup
DefaultDirName={pf}\{{NAME}}
DisableProgramGroupPage=yes
UninstallDisplayIcon={app}\{{NAME}}.exe
OutputDir=..\dist

[Tasks]
Name: "autostart"; Description: "Start {{NAME}} on session startup"; Flags: unchecked

[Files]
Source: "..\dist\{{NAME}}{{DEBUG}}\*"; DestDir: "{app}"; Flags: recursesubdirs

[Icons]
Name: "{commonprograms}\{{NAME}}"; Filename: "{app}\{{NAME}}.exe"
Name: "{commondesktop}\{{NAME}}"; Filename: "{app}\{{NAME}}.exe"
Name: "{userstartup}\{{NAME}}"; Filename: "{app}\{{NAME}}.exe"; Tasks: autostart
