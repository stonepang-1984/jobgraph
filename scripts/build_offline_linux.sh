#!/bin/bash
# ============================================================
# JobGraph 离线部署包构建脚本 (Linux)
# 使用 SQLite 存储，无需 Neo4j
# 使用规则模式，无需 PyTorch
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BUILD_DIR="/tmp/jobgraph-offline-build"
OUTPUT_DIR="$PROJECT_ROOT/dist"

echo "=========================================="
echo "构建 JobGraph 离线部署包"
echo "=========================================="
echo "项目根目录: $PROJECT_ROOT"

# 清理构建目录
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR" "$OUTPUT_DIR"

# 复制项目文件
echo "[1/5] 复制项目文件..."
cp -r "$PROJECT_ROOT/src" "$BUILD_DIR/"
cp -r "$PROJECT_ROOT/web" "$BUILD_DIR/"
cp -r "$PROJECT_ROOT/config" "$BUILD_DIR/"
cp -r "$PROJECT_ROOT/scripts" "$BUILD_DIR/"

# 只复制初始数据
mkdir -p "$BUILD_DIR/data"
if [ -d "$PROJECT_ROOT/data/initial" ]; then
    cp -r "$PROJECT_ROOT/data/initial" "$BUILD_DIR/data/"
fi

cp "$PROJECT_ROOT/requirements-lite.txt" "$BUILD_DIR/"
cp "$PROJECT_ROOT/streamlit_app.py" "$BUILD_DIR/"
cp "$PROJECT_ROOT/pyproject.toml" "$BUILD_DIR/" 2>/dev/null || true

# 创建 .env 配置
echo "[2/5] 创建配置文件..."
cat > "$BUILD_DIR/.env" << 'EOF'
# JobGraph 配置
STORAGE_BACKEND=sqlite
SQLITE_DB_PATH=data/jobgraph.db
USE_TORCH=false
DEMO_MODE=true
LOG_LEVEL=INFO
EOF

# 创建启动脚本
echo "[3/5] 创建启动脚本..."

# Linux 启动脚本
cat > "$BUILD_DIR/start.sh" << 'START_EOF'
#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "启动 JobGraph"
echo "=========================================="

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "错误: 未安装 Python3"
    echo "请运行: sudo apt install python3 python3-pip"
    exit 1
fi

# 检查依赖
echo "检查依赖..."
if ! python3 -c "import streamlit" 2>/dev/null; then
    echo "安装依赖..."
    pip3 install -r requirements-lite.txt -q
fi

# 初始化数据库
if [ ! -f "data/jobgraph.db" ]; then
    echo "初始化数据库..."
    python3 scripts/init_sqlite.py
fi

# 启动应用
echo "启动 Web 界面..."
echo "访问: http://localhost:8504"
python3 -m streamlit run streamlit_app.py --server.port 8504 --server.headless true
START_EOF
chmod +x "$BUILD_DIR/start.sh"

# Windows 启动脚本
cat > "$BUILD_DIR/start.bat" << 'BATCH_EOF'
@echo off
setlocal

cd /d "%~dp0"

echo ==========================================
echo 启动 JobGraph
echo ==========================================

REM 检查 Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 未安装 Python
    echo 请从 https://www.python.org/downloads/ 下载安装
    pause
    exit /b 1
)

REM 检查依赖
echo 检查依赖...
pip show streamlit >nul 2>&1
if %errorlevel% neq 0 (
    echo 安装依赖...
    pip install -r requirements-lite.txt -q
)

REM 初始化数据库
if not exist "data\jobgraph.db" (
    echo 初始化数据库...
    python scripts\init_sqlite.py
)

REM 启动应用
echo 启动 Web 界面...
echo 访问: http://localhost:8504
python -m streamlit run streamlit_app.py --server.port 8504 --server.headless true

pause
BATCH_EOF

# 创建 README
echo "[4/5] 创建说明文件..."
cat > "$BUILD_DIR/README.md" << 'README_EOF'
# JobGraph 离线部署包

## 功能特性

- 📄 简历上传解析
- 🎯 智能职位匹配
- 🔍 岗位搜索
- ⚠️ 避坑指南
- 🔒 隐私保护（数据本地存储）

## 系统要求

### Linux
- Python 3.8+
- pip

### Windows
- Python 3.8+（从 python.org 下载）
- pip（随 Python 安装）

## 快速启动

### Linux
```bash
chmod +x start.sh
./start.sh
```

### Windows
双击 `start.bat`

## 访问

启动后访问: http://localhost:8504

## 配置

编辑 `.env` 文件修改配置：
- `STORAGE_BACKEND`: 存储后端（sqlite/neo4j）
- `USE_TORCH`: 是否启用 PyTorch（默认关闭）
- `LOG_LEVEL`: 日志级别

## 数据

- 数据存储在 `data/jobgraph.db`（SQLite）
- 首次启动自动导入初始数据
README_EOF

# 打包
echo "[5/5] 打包..."

# Linux tar.gz
cd /tmp
tar -czf "$OUTPUT_DIR/jobgraph-offline-linux-x64.tar.gz" "jobgraph-offline-build"

# Windows zip (使用 zip 命令)
if command -v zip &> /dev/null; then
    cd "$BUILD_DIR"
    zip -r "$OUTPUT_DIR/jobgraph-offline-windows-x64.zip" . -x "*.pyc" -x "__pycache__/*"
else
    echo "警告: zip 命令不可用，跳过 Windows 包构建"
fi

# 清理
rm -rf "$BUILD_DIR"

echo ""
echo "=========================================="
echo "构建完成！"
echo "=========================================="
echo ""
echo "输出文件:"
ls -lh "$OUTPUT_DIR"/jobgraph-offline-* 2>/dev/null
echo ""
