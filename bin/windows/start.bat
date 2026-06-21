@echo off
REM ============================================================
REM JobGraph - Windows 启动脚本
REM ============================================================

setlocal

REM 获取安装目录
set INSTALL_DIR=%~dp0..
set APP_DIR=%INSTALL_DIR%\app
set RUNTIME_DIR=%INSTALL_DIR%\runtime

REM 运行时路径
set NEO4J_HOME=%RUNTIME_DIR%\neo4j
set REDIS_HOME=%RUNTIME_DIR%\redis
set PYTHON=%RUNTIME_DIR%\python\python.exe

REM 日志目录
set LOG_DIR=%INSTALL_DIR%\logs
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

REM PID 文件目录
set PID_DIR=%INSTALL_DIR%\pids
if not exist "%PID_DIR%" mkdir "%PID_DIR%"

echo ==========================================
echo 启动 JobGraph
echo ==========================================
echo 安装目录: %INSTALL_DIR%
echo.

REM ============================================================
REM 检查服务是否已运行
REM ============================================================
if exist "%PID_DIR%\neo4j.pid" (
    echo 服务已在运行，如需重启请先执行 stop.bat
    pause
    exit /b 0
)

REM ============================================================
REM 启动 Redis
REM ============================================================
echo [1/4] 启动 Redis...

REM 检查 Redis 是否已运行
redis-cli -p 6379 ping 2>nul | findstr "PONG" >nul
if %errorlevel% equ 0 (
    echo   Redis 已在运行
) else (
    start /B "%REDIS_HOME%\redis-server.exe"
    echo   Redis 已启动
)

REM ============================================================
REM 启动 Neo4j
REM ============================================================
echo [2/4] 启动 Neo4j...

REM 设置 Neo4j 环境
set NEO4J_HOME=%NEO4J_HOME%

REM 启动 Neo4j
start /B "%NEO4J_HOME%\bin\neo4j" console > "%LOG_DIR%\neo4j.log" 2>&1
echo %errorlevel% > "%PID_DIR%\neo4j.pid"
echo   Neo4j 已启动

REM 等待 Neo4j 启动
echo   等待 Neo4j 就绪...
timeout /t 15 /nobreak >nul
echo   Neo4j 已就绪

REM ============================================================
REM 初始化数据库
REM ============================================================
echo [3/4] 初始化数据库...

cd /d "%APP_DIR%"
"%PYTHON%" scripts\init_neo4j.py 2>nul
echo   数据库已初始化

REM 导入初始数据
if exist "data\initial\admin_data.json" (
    echo   导入初始数据...
    "%PYTHON%" scripts\import_from_admin.py --file data\initial\admin_data.json 2>nul
    echo   数据已导入
)

REM ============================================================
REM 启动 Web 界面
REM ============================================================
echo [4/4] 启动 Web 界面...

cd /d "%APP_DIR%"
start /B "%PYTHON%" -m streamlit run web\jobgraph.py --server.port 8504 --server.headless true > "%LOG_DIR%\streamlit.log" 2>&1
echo %errorlevel% > "%PID_DIR%\streamlit.pid"
echo   Web 界面已启动

REM ============================================================
REM 完成
REM ============================================================
echo.
echo ==========================================
echo JobGraph 启动完成！
echo ==========================================
echo.
echo 访问地址: http://localhost:8504
echo.
echo 服务状态:
echo   Redis:   运行中
echo   Neo4j:   运行中 (http://localhost:7474)
echo   Web UI:  运行中 (http://localhost:8504)
echo.
echo 停止服务: %INSTALL_DIR%\bin\stop.bat
echo.

pause
