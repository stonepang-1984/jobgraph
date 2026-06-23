@echo off
REM ============================================================
REM JobGraph - Windows 停止脚本
REM ============================================================

echo 停止 JobGraph...

REM 停止 Streamlit
taskkill /F /IM streamlit.exe 2>nul
taskkill /F /IM python.exe 2>nul

REM 停止 Neo4j
if exist "runtime\neo4j\bin\neo4j.bat" (
    call "runtime\neo4j\bin\neo4j.bat" stop 2>nul
)

echo.
echo JobGraph 已停止
echo.
pause
