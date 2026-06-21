; medicerti-vision Setup Script
; Inno Setup 6+ (https://jrsoftware.org/isinfo.php)

#define MyAppName "medicerti-vision"
#define MyAppDisplayName "Medicerti Vision"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "Medicerti Inc."
#define MyAppURL "https://medicerti.ai"
#define MyAppExeName "medicerti-vision.exe"
#define MyLauncherExeName "medicerti-launcher.exe"

[Setup]
AppId={{8E3B5C6D-1A2B-3C4D-5E6F-7A8B9C0D1E2F}
AppName={#MyAppDisplayName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppDisplayName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}/support
AppUpdatesURL={#MyAppURL}/updates
DefaultDirName={autopf64}\{#MyAppName}
DefaultGroupName={#MyAppDisplayName}
AllowNoIcons=yes
OutputDir=..\dist
OutputBaseFilename=medicerti-vision-setup-{#MyAppVersion}
SetupIconFile=..\brand\icon.ico
WizardImageFile=..\brand\wizard_sidebar.bmp
WizardSmallImageFile=..\brand\wizard_banner.bmp
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
DisableProgramGroupPage=yes
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppDisplayName}
VersionInfoDescription={#MyAppDisplayName} Installer
VersionInfoProductName={#MyAppDisplayName}
VersionInfoVersion={#MyAppVersion}
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "Korean"; MessagesFile: "compiler:Languages\Korean.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\dist\medicerti-vision.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\medicerti-launcher.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\version.json"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\brand\icon.ico"; DestDir: "{app}\brand"; Flags: ignoreversion

[Dirs]
Name: "{app}\data"; Permissions: users-modify
Name: "{app}\data\events"; Permissions: users-modify
Name: "{app}\data\reports"; Permissions: users-modify
Name: "{app}\data\snapshots"; Permissions: users-modify
Name: "{app}\logs"; Permissions: users-modify

[Icons]
Name: "{group}\{#MyAppDisplayName}"; Filename: "{app}\{#MyLauncherExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\brand\icon.ico"
Name: "{group}\{cm:UninstallProgram,{#MyAppDisplayName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppDisplayName}"; Filename: "{app}\{#MyLauncherExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\brand\icon.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyLauncherExeName}"; Description: "{cm:LaunchProgram,{#MyAppDisplayName}}"; Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "taskkill"; Parameters: "/f /im {#MyAppExeName}"; Flags: runhidden; RunOnceId: "KillServer"
Filename: "taskkill"; Parameters: "/f /im {#MyLauncherExeName}"; Flags: runhidden; RunOnceId: "KillLauncher"

[Code]
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    if not DirExists(ExpandConstant('{app}\data')) then
      CreateDir(ExpandConstant('{app}\data'));
  end;
end;

[Messages]
Korean.WelcomeLabel1=Medicerti Vision 설치 마법사
Korean.WelcomeLabel2=이 마법사는 [name/ver]을(를) 설치합니다.%n%n의료기관 전용 Edge AI 영상 분석 시스템입니다.%n낙상 감지 · 이상행동 탐지 · 출입 통제 기능을 제공합니다.%n%n설치를 시작하기 전에 다른 응용 프로그램을 모두 종료해 주십시오.
Korean.ClickNext=다음(N) >를 클릭하여 계속하거나 취소를 클릭하여 설치 프로그램을 닫으십시오.
Korean.FinishedHeadingLabel=[name] 설치 완료
Korean.FinishedLabel=설치가 성공적으로 완료되었습니다.%n%n[name]을 실행하면 웹 브라우저에서 대시보드가 자동으로 열립니다.%n기본 포트: 8111 (http://localhost:8111)
Korean.FinishedRestartLabel=설치를 완료하려면 컴퓨터를 재시작해야 합니다. 지금 재시작하시겠습니까?
