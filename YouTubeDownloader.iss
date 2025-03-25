#define MyAppName "YouTube 视频下载器"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "YouTubeDownloader"
#define MyAppURL ""
#define MyAppExeName "YouTubeDownloader.exe"
#define MyAppSourceDir "build\YouTubeDownloader"

[Setup]
AppId={{F5A83761-9C15-4A65-9E71-8B451F84A233}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DisableProgramGroupPage=yes
LicenseFile=license_zh.txt
OutputDir=installer
OutputBaseFilename=2
SetupIconFile=resources\youtube_logo.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma
SolidCompression=yes
WizardStyle=modern
; 默认使用中文界面
ShowLanguageDialog=no
; 确保中文显示正常
; 设置UTF-8编码以确保中文正常显示
; AllowUiAccess=yes
; 添加UTF-8编码支持
SetupLogging=yes
; 设置中文支持
SetupMutex=YouTubeDownloaderSetupMutex

[Languages]
Name: "chinesesimplified"; MessagesFile: "ChineseSimplified.isl"

; 设置默认语言为中文



[Messages]
; 中文界面文本设置
chinesesimplified.BeveledLabel=简体中文
chinesesimplified.ButtonNext=下一步(&N)
chinesesimplified.ButtonBack=上一步(&B)
chinesesimplified.ButtonCancel=取消(&C)
chinesesimplified.ButtonInstall=安装(&I)
chinesesimplified.ButtonFinish=完成(&F)
chinesesimplified.WelcomeLabel1=欢迎使用 %1 安装向导
chinesesimplified.WelcomeLabel2=这将在您的计算机上安装 %1。%n%n建议您在继续安装前关闭所有其他应用程序。
chinesesimplified.LicenseLabel1=许可协议
chinesesimplified.LicenseLabel2=请阅读以下许可协议，然后选择是否接受协议条款。
chinesesimplified.LicenseLabel3=请阅读以下许可协议。您必须接受协议条款才能继续安装。
chinesesimplified.LicenseAccepted=我接受协议(&A)
chinesesimplified.LicenseNotAccepted=我不接受协议(&D)
chinesesimplified.WizardSelectDir=选择安装位置
chinesesimplified.SelectDirLabel1=安装程序将安装 %1 到以下文件夹。
chinesesimplified.SelectDirLabel2=要继续安装，请点击"下一步"。如果您想选择其他文件夹，请点击"浏览"。
chinesesimplified.SelectDirBrowseLabel=要继续安装，请点击"下一步"。如果您想选择其他文件夹，请点击"浏览"。
chinesesimplified.ReadyLabel1=安装程序已准备好开始安装 %1。
chinesesimplified.ReadyLabel2=点击"安装"继续安装。如果您想查看或更改任何设置，请点击"上一步"
chinesesimplified.UninstallAppFullTitle=卸载 %1
chinesesimplified.UninstallAppText=确定要完全删除 %1 及其所有组件吗？
chinesesimplified.UninstallStatusLabel=正在卸载 %1，请稍候...
chinesesimplified.UninstalledAll=%1 已成功地从您的计算机移除。

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "{#MyAppSourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent