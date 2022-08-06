[Setup]
AppName={#GetEnv("NAME")}
AppVersion={#GetEnv("VERSION")}
OutputBaseFilename={#GetEnv("NAME")}{#GetEnv("DEBUG")}-setup
DefaultDirName={pf}\{#GetEnv("NAME")}
DisableProgramGroupPage=yes
UninstallDisplayIcon={app}\{#GetEnv("NAME")}.exe
OutputDir=..\dist

[Tasks]
Name: "autostart"; Description: "Start {#GetEnv("NAME")} on session startup"; Flags: unchecked

[Files]
Source: "..\dist\{#GetEnv('NAME')}{#GetEnv('DEBUG')}\*"; DestDir: "{app}"; Flags: recursesubdirs

[Icons]
Name: "{commonprograms}\{#GetEnv('NAME')}"; Filename: "{app}\{#GetEnv('NAME')}.exe"
Name: "{commondesktop}\{#GetEnv('NAME')}"; Filename: "{app}\{#GetEnv('NAME')}.exe"
Name: "{userstartup}\{#GetEnv('NAME')}"; Filename: "{app}\{#GetEnv('NAME')}.exe"; Tasks: autostart
