@echo off
REM ============================================================
REM JobGraph 离线部署包构建脚本 (Windows)
REM 使用 SQLite 存储，无需 Neo4j
REM 使用规则模式，无需 PyTorch
REM ============================================================

setlocal

set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%
set BUILD_DIR=%PROJECT_ROOT%dist\jobgraph-offline
set OUTPUT_DIR=%PROJECT_ROOT%dist

echo ==========================================
echo 构建 JobGraph 离线部署包
echo ==========================================

REM 清理构建目录
if exist "%BUILD_DIR%" rmdir /s /q "%BUILD_DIR%"
mkdir "%BUILD_DIR%"

REM 复制项目文件
echo [1/4] 复制项目文件...
xcopy /E /I /Q src "%BUILD_DIR%\src"
xcopy /E /I /Q web "%BUILD_DIR%\web"
xcopy /E /I /Q config "%BUILD_DIR%\config"
xcopy /E /I /Q scripts "%BUILD_DIR%\scripts"
xcopy /E /I /Q data "%BUILD_DIR%\data"
copy requirements-lite.txt "%BUILD_DIR%\"
copy streamlit_app.py "%BUILD_DIR%\"
copy pyproject.toml "%BUILD_DIR%\" 2>nul

REM 创建 .env 配置
echo [2/4] 创建配置文件...
(
echo # JobGraph 配置
echo STORAGE_BACKEND=sqlite
echo SQLITE_DB_PATH=data/jobgraph.db
echo USE_TORCH=false
echo DEMO_MODE=true
echo LOG_LEVEL=INFO
) > "%BUILD_DIR%\.env"

REM 创建启动脚本
echo [3/4] 创建启动脚本...
(
echo @echo off
echo setlocal
echo.
echo cd /d "%%~dp0"
echo.
echo ==========================================
echo 启动 JobGraph
echo ==========================================
echo.
echo REM 检查 Python
echo python --version ^>nul 2^>^&1
echo if %%errorlevel%% neq 0 ^(
echo     echo 错误: 未安装 Python
echo     echo 请从 https://www.python.org/downloads/ 下载安装
echo     pause
echo     exit /b 1
echo ^)
echo.
echo REM 检查依赖
echo echo 检查依赖...
echo pip show streamlit ^>nul 2^>^&1
echo if %%errorlevel%% neq 0 ^(
echo     echo 安装依赖...
echo     pip install -r requirements-lite.txt -q
echo ^)
echo.
echo REM 初始化数据库
echo if not exist "data\jobgraph.db" ^(
echo     echo 初始化数据库...
echo     python scripts\init_sqlite.py
echo ^)
echo.
echo REM 启动应用
echo echo 启动 Web 界面...
echo echo 访问: http://localhost:8504
echo python -m streamlit run streamlit_app.py --server.port 8504 --server.headless true
echo.
echo pause
) > "%BUILD_DIR%\start.bat"

REM 创建 ZIP 包
echo [4/4] 打包...
cd "%OUTPUT_DIR%"
powershell -Command "Compress-Archive -Path '%BUILD_DIR%' -DestinationPath '%OUTPUT_DIR%\jobgraph-offline-windows-x64.zip' -Force"

echo.
echo ==========================================
echo 构建完成！
echo ==========================================
echo.
echo 输出文件:
echo   %OUTPUT_DIR%\jobgraph-offline-windows-x64.zip
echo.
echo 使用方法:
echo   1. 解压 ZIP 文件
echo   2. 双击 start.bat
echo.

pause
