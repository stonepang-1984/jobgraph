@echo off
REM ============================================================
REM JobGraph - Windows 一键安装脚本
REM 双击运行，自动安装依赖并启动服务
REM ============================================================

setlocal enabledelayedexpansion

echo ==========================================
echo JobGraph - Windows 一键安装
echo ==========================================
echo.

REM 获取脚本目录
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

REM ============================================================
REM 检查 Python
REM ============================================================
echo [1/5] 检查 Python...

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python 未安装！
    echo.
    echo 请先安装 Python 3.10+：
    echo   https://www.python.org/downloads/
    echo.
    echo 安装时请勾选 "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo   Python %PYTHON_VERSION% 已安装

REM ============================================================
REM 创建虚拟环境
REM ============================================================
echo.
echo [2/5] 创建虚拟环境...

if exist "venv" (
    echo   虚拟环境已存在
) else (
    python -m venv venv
    echo   虚拟环境已创建
)

REM 激活虚拟环境
call venv\Scripts\activate.bat

REM ============================================================
REM 安装依赖
REM ============================================================
echo.
echo [3/5] 安装 Python 依赖（首次安装需要几分钟）...

pip install --upgrade pip -q
pip install -r requirements.txt

echo   依赖安装完成

REM ============================================================
REM 下载 Neo4j
REM ============================================================
echo.
echo [4/5] 准备 Neo4j...

if exist "runtime\neo4j\bin\neo4j.bat" (
    echo   Neo4j 已存在
) else (
    echo   下载 Neo4j（约 400MB）...
    mkdir runtime 2>nul
    
    powershell -Command "Invoke-WebRequest -Uri 'https://dist.neo4j.org/neo4j-community-5.26.0-windows.zip' -OutFile 'neo4j.zip'"
    powershell -Command "Expand-Archive -Path 'neo4j.zip' -DestinationPath 'runtime'"
    ren "runtime\neo4j-community-5.26.0" "neo4j"
    del neo4j.zip
    
    echo   Neo4j 下载完成
)

REM ============================================================
REM 创建启动脚本
REM ============================================================
echo.
echo [5/5] 创建启动脚本...

(
echo @echo off
echo echo ==========================================
echo echo 启动 JobGraph
echo echo ==========================================
echo echo.
echo.
echo REM 激活虚拟环境
echo call "%%~dp0venv\Scripts\activate.bat"
echo.
echo REM 设置 Neo4j 环境
echo set NEO4J_HOME=%%~dp0runtime\neo4j
echo.
echo REM 启动 Neo4j
echo echo [1/3] 启动 Neo4j...
echo start /B "%%NEO4J_HOME%%\bin\neo4j.bat" console
echo timeout /t 15 /nobreak ^>nul
echo echo   Neo4j 已启动
echo.
echo REM 初始化数据库
echo echo [2/3] 初始化数据库...
echo cd /d "%%~dp0"
echo python scripts\init_neo4j.py 2^>nul
echo if exist "data\initial\admin_data.json" (
echo     python scripts\import_from_admin.py --file data\initial\admin_data.json 2^>nul
echo )
echo echo   数据库已初始化
echo.
echo REM 启动 Web 界面
echo echo [3/3] 启动 Web 界面...
echo start /B python -m streamlit run web\jobgraph.py --server.port 8504 --server.headless true
echo.
echo echo.
echo echo ==========================================
echo echo JobGraph 启动完成！
echo echo =================================echo 访问: http://localhost:8504
echo 停止: 运行 stop.bat
echo ==========================================
echo echo.
echo pause
) > start.bat

(
echo @echo off
echo echo 停止 JobGraph...
echo.
echo REM 停止 Streamlit
echo taskkill /F /IM streamlit.exe 2^>nul
echo taskkill /F /IM python.exe 2^>nul
echo.
echo REM 停止 Neo4j
echo if exist "runtime\neo4j\bin\neo4j.bat" (
echo     call "runtime\neo4j\bin\neo4j.bat" stop
echo )
echo.
echo echo JobGraph 已停止
echo pause
) > stop.bat

echo   启动脚本已创建

REM ============================================================
REM 完成
REM ============================================================
echo.
echo ==========================================
echo 安装完成！
echo ==========================================
echo.
echo 启动方式：
echo   双击 start.bat
echo.
echo 访问地址：
echo   http://localhost:8504
echo.
echo 首次启动需要几分钟初始化数据库
echo.

pause
