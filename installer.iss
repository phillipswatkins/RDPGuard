; Zopi Guard - Inno Setup Script
; Builds a professional Windows installer

#define AppName "Zopi Guard"
#define AppVersion "1.0.0"
#define AppPublisher "Zopi Ltd"
#define AppURL "https://zopi.uk"
#define AppExeName "ZopiGuard.exe"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} v{#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
AppUpdatesURL=https://github.com/phillipswatkins/RDPGuard/releases
DefaultDirName={autopf}\ZopiGuard
DefaultGroupName={#AppName}
AllowNoIcons=yes
; Require admin for firewall access
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=installer_output
OutputBaseFilename=ZopiGuardSetup-v{#AppVersion}
SetupIconFile=assets\shield.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
WizardSmallImageFile=assets\installer_banner.bmp
; Minimum Windows version: Windows 10
MinVersion=10.0
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
UninstallDisplayIcon={app}\{#AppExeName}
UninstallDisplayName={#AppName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon";     Description: "Create a &desktop shortcut";          GroupDescription: "Additional shortcuts:"; Flags: checked
Name: "startupicon";     Description: "Launch Zopi Guard when Windows starts"; GroupDescription: "Additional shortcuts:"; Flags: unchecked
Name: "startmenuicon";   Description: "Create a Start &Menu shortcut";        GroupDescription: "Additional shortcuts:"; Flags: checked

[Files]
; Main application (built by PyInstaller)
Source: "dist\ZopiGuard\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Start Menu
Name: "{group}\{#AppName}";          Filename: "{app}\{#AppExeName}"; Comment: "Zopi Guard — RDP Brute Force Protection"
Name: "{group}\Uninstall {#AppName}"; Filename: "{uninstallexe}"

; Desktop shortcut
Name: "{autodesktop}\{#AppName}";    Filename: "{app}\{#AppExeName}"; Tasks: desktopicon; Comment: "Zopi Guard — RDP Brute Force Protection"

; Startup (runs minimised to tray)
Name: "{userstartup}\{#AppName}";    Filename: "{app}\{#AppExeName}"; Parameters: "--minimised"; Tasks: startupicon

[Run]
; Launch after install
Filename: "{app}\{#AppExeName}"; Description: "Launch {#AppName}"; Flags: nowait postinstall skipifsilent

[UninstallRun]
; Clean up firewall rules on uninstall
Filename: "powershell.exe"; Parameters: "-NoProfile -Command ""Get-NetFirewallRule -DisplayName 'ZopiGuard_Block_*' | Remove-NetFirewallRule"""; Flags: runhidden

[Messages]
WelcomeLabel1=Welcome to the [name] Setup Wizard
WelcomeLabel2=This will install [name/ver] on your computer.%n%nZopi Guard protects your Windows RDP server from brute-force attacks by monitoring login failures and automatically blocking offending IP addresses.%n%nClick Next to continue.

[Code]
// Check if running Windows 10 or later
function InitializeSetup(): Boolean;
var
  Version: TWindowsVersion;
begin
  GetWindowsVersionEx(Version);
  if Version.Major < 10 then
  begin
    MsgBox('Zopi Guard requires Windows 10 or later.', mbError, MB_OK);
    Result := False;
  end else
    Result := True;
end;
