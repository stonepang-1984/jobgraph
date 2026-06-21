; ============================================================
; JobGraph - Inno Setup 配置文件
; Windows 安装程序配置
; ============================================================

[Setup]
AppName=JobGraph
AppVersion=1.0.0
AppPublisher=JobGraph
AppPublisherURL=https://github.com/stonepang-1984/jobgraph
DefaultDirName={autopf}\JobGraph
DefaultGroupName=JobGraph
OutputBaseFilename=JobGraph-Setup-Windows-x64
Compression=lzma2
SolidCompression=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest
SetupIconFile=..\docs\logo.ico
UninstallDisplayIcon={app}\bin\start.bat

[Files]
; 运行时依赖
Source: "..\deps\windows\runtime\python\*"; DestDir: "{app}\runtime\python"; Flags: recursesubdirs ignoreversion
Source: "..\deps\windows\runtime\neo4j\*"; DestDir: "{app}\runtime\neo4j"; Flags: recursesubdirs ignoreversion
Source: "..\deps\windows\runtime\redis\*"; DestDir: "{app}\runtime\redis"; Flags: recursesubdirs ignoreversion

; 应用程序
Source: "..\app\*"; DestDir: "{app}\app"; Flags: recursesubdirs ignoreversion

; 启动脚本
Source: "..\bin\windows\start.bat"; DestDir: "{app}\bin"
Source: "..\bin\windows\stop.bat"; DestDir: "{app}\bin"

; 初始数据
Source: "..\data\initial\*"; DestDir: "{app}\app\data\initial"; Flags: recursesubdirs ignoreversion

[Dirs]
Name: "{app}\logs"
Name: "{app}\pids"
Name: "{app}\data\redis"
Name: "{app}\app\data\user"

[Icons]
Name: "{group}\JobGraph"; Filename: "{app}\bin\start.bat"; IconFilename: "{app}\runtime\neo4j\bin\neo4j-icon.ico"
Name: "{group}\停止 JobGraph"; Filename: "{app}\bin\stop.bat"
Name: "{group}\卸载 JobGraph"; Filename: "{uninstallexe}"
Name: "{commondesktop}\JobGraph"; Filename: "{app}\bin\start.bat"; IconFilename: "{app}\runtime\neo4j\bin\neo4j-icon.ico"

[Run]
Filename: "{app}\bin\start.bat"; Description: "启动 JobGraph"; Flags: postinstall nowait

[UninstallRun]
Filename: "{app}\bin\stop.bat"; RunOnceId: "StopJobGraph"

[UninstallDelete]
Type: filesandordirs; Name: "{app}\logs"
Type: filesandordirs; Name: "{app}\pids"
Type: filesandordirs; Name: "{app}\data\redis"
