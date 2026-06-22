@echo off
REM ============================================================
REM JobGraph - Windows 离线安装包构建脚本
REM 打包所有依赖，用户无需联网即可安装
REM ============================================================

setlocal

set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%\..\..
set BUILD_DIR=%PROJECT_ROOT%\build\windows-offline
set DEPS_DIR=%PROJECT_ROOT%\deps\windows

echo ==========================================
echo 构建 Windows 离线安装包
echo ==========================================

REM ============================================================
REM 检查依赖
REM ============================================================
echo [1/6] 检查依赖...

if not exist "%DEPS_DIR%\python" (
    echo 错误: 缺少 Python 依赖
    echo 请先运行: installer\windows\download-deps.bat
    pause
    exit /b 1
)

if not exist "%DEPS_DIR%\neo4j" (
    echo 错误: 缺少 Neo4j 依赖
    pause
    exit /b 1
)

if not exist "%DEPS_DIR%\redis" (
    echo 错误: 缺少 Redis 依赖
    pause
    exit /b 1
)

echo   依赖检查通过

REM ============================================================
REM 清理构建目录
REM ============================================================
echo [2/6] 清理构建目录...

if exist "%BUILD_DIR%" rmdir /S /Q "%BUILD_DIR%"
mkdir "%BUILD_DIR%"

REM ============================================================
REM 复制运行时依赖
REM ============================================================
echo [3/6] 复制运行时依赖...

xcopy /E /I /Q "%DEPS_DIR%\python" "%BUILD_DIR%\runtime\python"
xcopy /E /I /Q "%DEPS_DIR%\neo4j" "%BUILD_DIR%\runtime\neo4j"
xcopy /E /I /Q "%DEPS_DIR%\redis" "%BUILD_DIR%\runtime\redis"

REM 清理不需要的文件
if exist "%BUILD_DIR%\runtime\python\test" rmdir /S /Q "%BUILD_DIR%\runtime\python\test"
if exist "%BUILD_DIR%\runtime\python\Doc" rmdir /S /Q "%BUILD_DIR%\runtime\python\Doc"
if exist "%BUILD_DIR%\runtime\neo4j\logs" rmdir /S /Q "%BUILD_DIR%\runtime\neo4j\logs"
if exist "%BUILD_DIR%\runtime\neo4j\data" rmdir /S /Q "%BUILD_DIR%\runtime\neo4j\data"

echo   运行时依赖已复制

REM ============================================================
REM 下载 Python 依赖（离线包）
REM ============================================================
echo [4/6] 准备 Python 依赖...

set PYTHON=%BUILD_DIR%\runtime\python\python.exe
set PIP_DIR=%BUILD_DIR%\app\lib\python

mkdir "%PIP_DIR%"

echo   下载 Python 依赖...
"%PYTHON%" -m pip download -r "%PROJECT_ROOT%\requirements.txt" -d "%PIP_DIR%" 2>nul

echo   Python 依赖已准备

REM ============================================================
REM 复制应用程序
REM ============================================================
echo [5/6] 复制应用程序...

mkdir "%BUILD_DIR%\app"
xcopy /E /I /Q "%PROJECT_ROOT%\src" "%BUILD_DIR%\app\src"
xcopy /E /I /Q "%PROJECT_ROOT%\web" "%BUILD_DIR%\app\web"
xcopy /E /I /Q "%PROJECT_ROOT%\config" "%BUILD_DIR%\app\config"
xcopy /E /I /Q "%PROJECT_ROOT%\scripts" "%BUILD_DIR%\app\scripts"
xcopy /E /I /Q "%PROJECT_ROOT%\api" "%BUILD_DIR%\app\api"
copy "%PROJECT_ROOT%\requirements.txt" "%BUILD_DIR%\app\"
copy "%PROJECT_ROOT%\pyproject.toml" "%BUILD_DIR%\app\"

REM 复制初始数据
if exist "%PROJECT_ROOT%\data\initial" xcopy /E /I /Q "%PROJECT_ROOT%\data\initial" "%BUILD_DIR%\app\data\initial"

REM 复制启动脚本
mkdir "%BUILD_DIR%\bin"
copy "%PROJECT_ROOT%\bin\windows\*.bat" "%BUILD_DIR%\bin\"

echo   应用程序已复制

REM ============================================================
REM 创建 Inno Setup 配置
REM ============================================================
echo [6/6] 创建安装程序...

(
echo [Setup]
echo AppName=JobGraph
echo AppVersion=1.0.0
echo AppPublisher=JobGraph
echo DefaultDirName={autopf}\JobGraph
echo DefaultGroupName=JobGraph
echo OutputBaseFilename=JobGraph-Setup-Windows-x64-Offline
echo Compression=lzma2
echo SolidCompression=yes
echo ArchitecturesAllowed=x64compatible
echo ArchitecturesInstallIn64BitMode=x64compatible
echo.
echo [Files]
echo Source: "%BUILD_DIR%\runtime\*"; DestDir: "{app}\runtime"; Flags: recursesubdirs ignoreversion
echo Source: "%BUILD_DIR%\app\*"; DestDir: "{app}\app"; Flags: recursesubdirs ignoreversion
echo Source: "%BUILD_DIR%\bin\*"; DestDir: "{app}\bin"; Flags: recursesubdirs ignoreversion
echo.
echo [Dirs]
echo Name: "{app}\logs"
echo Name: "{app}\pids"
echo Name: "{app}\data\redis"
echo Name: "{app}\app\data\user"
echo.
echo [Icons]
echo Name: "{group}\JobGraph"; Filename: "{app}\bin\start.bat"
echo Name: "{group}\停止 JobGraph"; Filename: "{app}\bin\stop.bat"
echo Name: "{group}\卸载 JobGraph"; Filename: "{uninstallexe}"
echo Name: "{commondesktop}\JobGraph"; Filename: "{app}\bin\start.bat"
echo.
echo [Run]
echo Filename: "{app}\bin\start.bat"; Description: "启动 JobGraph"; Flags: postinstall nowait
echo.
echo [UninstallRun]
echo Filename: "{app}\bin\stop.bat"; RunOnceId: "StopJobGraph"
echo.
echo [UninstallDelete]
echo Type: filesandordirs; Name: "{app}\logs"
echo Type: filesandordirs; Name: "{app}\pids"
echo Type: filesandordirs; Name: "{app}\data\redis"
) > "%BUILD_DIR%\jobgraph-offline.iss"

REM 编译安装程序
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" "%BUILD_DIR%\jobgraph-offline.iss"
    echo.
    echo ==========================================
    echo 离线安装包创建完成！
    echo ==========================================
    echo.
    echo 输出文件: Output\JobGraph-Setup-Windows-x64-Offline.exe
    echo.
) else (
    echo 错误: 未安装 Inno Setup
    echo 请先安装: https://jrsoftware.org/isinfo.php
    echo.
    echo 或者手动编译: "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" %BUILD_DIR%\jobgraph-offline.iss
)

pause
