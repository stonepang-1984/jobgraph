@echo off
REM ============================================================
REM JobGraph - Windows 依赖下载脚本
REM 下载 Python、Neo4j、Redis 的 Windows 版本
REM ============================================================

setlocal

set SCRIPT_DIR=%~dp0
set DEPS_DIR=%SCRIPT_DIR%\..\deps\windows

if not exist "%DEPS_DIR%" mkdir "%DEPS_DIR%"
cd /d "%DEPS_DIR%"

echo ==========================================
echo 下载 Windows 依赖
echo ==========================================

REM Python 版本
set PYTHON_VERSION=3.11.9
set PYTHON_DIR=python

REM Neo4j 版本
set NEO4J_VERSION=5.26.0
set NEO4J_DIR=neo4j

REM Redis 版本 (使用 Memurai 或 Redis-x64)
set REDIS_VERSION=5.0.14.1
set REDIS_DIR=redis

REM ============================================================
REM 下载 Python Embeddable
REM ============================================================
echo.
echo [1/3] 下载 Python %PYTHON_VERSION%...

if exist "%PYTHON_DIR%" (
    echo   Python 已存在，跳过下载
) else (
    set PYTHON_URL=https://www.python.org/ftp/python/%PYTHON_VERSION%/python-%PYTHON_VERSION%-embed-amd64.zip
    echo   下载: %PYTHON_URL%
    curl -L -o python.zip "%PYTHON_URL%"
    mkdir "%PYTHON_DIR%"
    cd "%PYTHON_DIR%"
    powershell -command "Expand-Archive -Path '..\python.zip' -DestinationPath '.'"
    cd ..
    del python.zip
    echo   Python 下载完成
)

REM ============================================================
REM 下载 Neo4j
REM ============================================================
echo.
echo [2/3] 下载 Neo4j %NEO4J_VERSION%...

if exist "%NEO4J_DIR%" (
    echo   Neo4j 已存在，跳过下载
) else (
    set NEO4J_URL=https://dist.neo4j.org/neo4j-community-%NEO4J_VERSION%-windows.zip
    echo   下载: %NEO4J_URL%
    curl -L -o neo4j.zip "%NEO4J_URL%"
    powershell -command "Expand-Archive -Path 'neo4j.zip' -DestinationPath '.'"
    ren "neo4j-community-%NEO4J_VERSION%" "%NEO4J_DIR%"
    del neo4j.zip
    echo   Neo4j 下载完成
)

REM ============================================================
REM 下载 Redis (Windows 版本)
REM ============================================================
echo.
echo [3/3] 下载 Redis %REDIS_VERSION%...

if exist "%REDIS_DIR%" (
    echo   Redis 已存在，跳过下载
) else (
    set REDIS_URL=https://github.com/tporadowski/redis/releases/download/v%REDIS_VERSION%/Redis-x64-%REDIS_VERSION%.zip
    echo   下载: %REDIS_URL%
    curl -L -o redis.zip "%REDIS_URL%"
    mkdir "%REDIS_DIR%"
    cd "%REDIS_DIR%"
    powershell -command "Expand-Archive -Path '..\redis.zip' -DestinationPath '.'"
    cd ..
    del redis.zip
    echo   Redis 下载完成
)

echo.
echo ==========================================
echo 所有依赖下载完成！
echo ==========================================
echo.
echo 目录结构:
echo   %DEPS_DIR%\
echo   ├── python\    Python %PYTHON_VERSION%
echo   ├── neo4j\     Neo4j %NEO4J_VERSION%
echo   └── redis\     Redis %REDIS_VERSION%
echo.

endlocal
