@echo off
REM ============================================================
REM JobGraph - Windows 停止脚本
REM ============================================================

setlocal

REM 获取安装目录
set INSTALL_DIR=%~dp0..
set RUNTIME_DIR=%INSTALL_DIR%\runtime
set PID_DIR=%INSTALL_DIR%\pids

echo ==========================================
echo 停止 JobGraph
echo ==========================================
echo.

REM ============================================================
REM 停止 Web 界面
REM ============================================================
echo [1/3] 停止 Web 界面...

if exist "%PID_DIR%\streamlit.pid" (
    taskkill /F /IM streamlit.exe >nul 2>&1
    del "%PID_DIR%\streamlit.pid"
    echo   Web 界面已停止
) else (
    echo   Web 界面未运行
)

REM ============================================================
REM 停止 Neo4j
REM ============================================================
echo [2/3] 停止 Neo4j...

if exist "%PID_DIR%\neo4j.pid" (
    "%RUNTIME_DIR%\neo4j\bin\neo4j" stop >nul 2>&1
    del "%PID_DIR%\neo4j.pid"
    echo   Neo4j 已停止
) else (
    echo   Neo4j 未运行
)

REM ============================================================
REM 停止 Redis
REM ============================================================
echo [3/3] 停止 Redis...

redis-cli -p 6379 ping 2>nul | findstr "PONG" >nul
if %errorlevel% equ 0 (
    redis-cli -p 6379 shutdown >nul 2>&1
    echo   Redis 已停止
) else (
    echo   Redis 未运行
)

REM ============================================================
REM 完成
REM ============================================================
echo.
echo ==========================================
echo JobGraph 已停止
echo ==========================================
echo.

pause
