; ================================================================
; מתקין תוכנות בקליק v5.4 — סקריפט התקנה (Inno Setup)
; ממשק עברי מלא באמצעות Hebrew.isl
; ================================================================
;
; הוראות שימוש:
; 1. התקן Inno Setup (https://jrsoftware.org/isinfo.php)
; 2. ודא שקובץ Hebrew.isl נמצא בתיקיית Languages של Inno Setup
;    (אם אינו קיים - הורד מ: https://jrsoftware.org/files/istrans/)
;    והנח אותו ב: C:\Program Files (x86)\Inno Setup 6\Languages\Hebrew.isl
; 3. ערוך את הנתיבים בסעיף [Files] בהתאם למבנה התיקייה שלך (לאחר build.bat)
; 4. פתח קובץ זה ב-Inno Setup Compiler ולחץ Build (F9)
;
; ================================================================

#define MyAppName "מתקין תוכנות בקליק"
#define MyAppNameEn "SoftInstaller"
#define MyAppVersion "5.4"
#define MyAppPublisher "SoftInstaller"
#define MyAppExeName "SoftInstaller.exe"
#define MyAppIcon "app_icon.ico"

[Setup]
; מזהה ייחודי לאפליקציה - אל תשנה לאחר הפצה ראשונה
AppId={{B4E1A9F3-7C2D-4A8E-9F1B-3D5C6E8A2F40}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppNameEn}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
; דורש הרשאות מנהל (Administrator) להתקנה ולהרצה - חיוני לזיהוי תוכנות והתקנות בפועל
PrivilegesRequired=admin
OutputDir=installer_output
OutputBaseFilename=SoftInstaller_Setup_v{#MyAppVersion}
SetupIconFile={#MyAppIcon}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
; כיוון RTL מלא לאשף ההתקנה
RTLLanguage=yes
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
; שימוש בקובץ Hebrew.isl - ממשק עברי מלא, כולל RTL
Name: "hebrew"; MessagesFile: "compiler:Languages\Hebrew.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1

[Files]
; ===== מצב תיקיית הפצה (onedir) - ברירת מחדל מה-build.bat (אופציה 1) =====
Source: "dist\SoftInstaller\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\SoftInstaller\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; אם קומפלת במצב קובץ יחיד (onefile, אופציה 2 ב-build.bat), השתמש בשורות הבאות במקום
; (הסר ; מההתחלה והסר את שתי השורות שמעליהן):
; Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
; Source: "dist\icons\*"; DestDir: "{app}\icons"; Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist

; קובץ אייקון לקיצורי דרך
Source: "{#MyAppIcon}"; DestDir: "{app}"; Flags: ignoreversion

; קובץ README (אופציונלי, אם קיים)
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion isreadme skipifsourcedoesntexist

; הערה: תיקיות software\ (כולל config.json), icons\, reports\ נוצרות אוטומטית
; בהרצה הראשונה ע"י main.py. אם רוצים לארוז מראש קבצי התקנה וקטגוריות קיימות,
; ניתן להוסיף שורה כזו (הסר את ה-; כדי להפעיל):
; Source: "software\*"; DestDir: "{app}\software"; Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppIcon}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppIcon}"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

[Run]
; אפשרות להריץ את התוכנה מיד בסיום ההתקנה (טקסט מתורגם אוטומטית ע"י Hebrew.isl)
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; מחיקת קבצים שנוצרו בזמן ריצה בעת הסרת ההתקנה (אופציונלי - הסר הערה אם רוצים מחיקה מלאה)
; Type: filesandordirs; Name: "{app}\reports"
; Type: files; Name: "{app}\software\config.json"
; Type: files; Name: "{app}\.session.json"

[Code]
function InitializeSetup(): Boolean;
begin
  Result := True;
end;
