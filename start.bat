@echo off
REM ============================================================
REM JobGraph - Windows 启动脚本
REM ============================================================

echo ==========================================
echo 启动 JobGraph
echo ==========================================
echo.

REM 获取脚本目录
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

REM 激活虚拟环境
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo 错误: 虚拟环境不存在，请先运行 install.bat
    pause
    exit /b 1
)

REM 设置 Neo4j 环境
set NEO4J_HOME=%SCRIPT_DIR%runtime\neo4j

REM 启动 Neo4j
echo [1/3] 启动 Neo4j...
if exist "%NEO4J_HOME%\bin\neo4j.bat" (
    start "Neo4j" /B "%NEO4J_HOME%\bin\neo4j.bat" console
    echo   等待 Neo4j 启动...
    timeout /t 15 /nobreak >nul
    echo   Neo4j 已启动
) else (
    echo   警告: Neo4j 未安装
)

REM 初始化数据库
echo [2/3] 初始化数据库...
python scripts\init_neo4j.py 2>nul
if exist "data\initial\admin_data.json" (
    python scripts\import_from_admin.py --file data\initial\admin_data.json 2>nul
)
echo   数据库已初始化

REM 启动 Web 界面
echo [3/3] 启动 Web 界面...
start "JobGraph Web" /B python -m streamlit run web\jobgraph.py --server.port 8504 --server.headless true
echo   Web 界面已启动

echo.
echo ==========================================
echo JobGraph 启动完成！
echo ==========================================
echo 访问: http://localhost:8504
echo 停止: 运行 stop.bat
echo ==========================================
echo.
pause
