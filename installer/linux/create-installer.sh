#!/bin/bash
# ============================================================
# JobGraph - Linux 打包脚本
# 创建自解压安装包
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR/../.."
BUILD_DIR="$PROJECT_ROOT/build/linux"
OUTPUT_DIR="$PROJECT_ROOT/dist"

echo "=========================================="
echo "创建 Linux 安装包"
echo "=========================================="

# ============================================================
# 清理构建目录
# ============================================================
echo "[1/5] 清理构建目录..."
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"
mkdir -p "$OUTPUT_DIR"

# ============================================================
# 复制运行时依赖
# ============================================================
echo "[2/5] 复制运行时依赖..."

DEPS_DIR="$PROJECT_ROOT/deps/linux"

if [ ! -d "$DEPS_DIR" ]; then
    echo "错误: 依赖目录不存在，请先运行 installer/linux/download-deps.sh"
    exit 1
fi

# 复制 Python
if [ -d "$DEPS_DIR/python" ]; then
    cp -r "$DEPS_DIR/python" "$BUILD_DIR/runtime/"
    echo "  Python 已复制"
else
    echo "错误: Python 未下载"
    exit 1
fi

# 复制 Neo4j
if [ -d "$DEPS_DIR/neo4j" ]; then
    cp -r "$DEPS_DIR/neo4j" "$BUILD_DIR/runtime/"
    echo "  Neo4j 已复制"
else
    echo "错误: Neo4j 未下载"
    exit 1
fi

# 复制 Redis
if [ -d "$DEPS_DIR/redis" ]; then
    cp -r "$DEPS_DIR/redis" "$BUILD_DIR/runtime/"
    echo "  Redis 已复制"
else
    echo "错误: Redis 未下载"
    exit 1
fi

# ============================================================
# 复制应用程序
# ============================================================
echo "[3/5] 复制应用程序..."

# 复制源代码
mkdir -p "$BUILD_DIR/app"
cp -r "$PROJECT_ROOT/src" "$BUILD_DIR/app/"
cp -r "$PROJECT_ROOT/web" "$BUILD_DIR/app/"
cp -r "$PROJECT_ROOT/config" "$BUILD_DIR/app/"
cp -r "$PROJECT_ROOT/scripts" "$BUILD_DIR/app/"
cp -r "$PROJECT_ROOT/data/initial" "$BUILD_DIR/app/data/" 2>/dev/null || mkdir -p "$BUILD_DIR/app/data/initial"
cp -r "$PROJECT_ROOT/api" "$BUILD_DIR/app/"
cp -r "$PROJECT_ROOT/requirements.txt" "$BUILD_DIR/app/"
cp -r "$PROJECT_ROOT/pyproject.toml" "$BUILD_DIR/app/"

# 复制启动脚本
mkdir -p "$BUILD_DIR/bin"
cp -r "$PROJECT_ROOT/bin/linux/"* "$BUILD_DIR/bin/"
chmod +x "$BUILD_DIR/bin/"*.sh

echo "  应用程序已复制"

# ============================================================
# 创建安装脚本
# ============================================================
echo "[4/5] 创建安装脚本..."

cat > "$BUILD_DIR/install.sh" << 'INSTALL_EOF'
#!/bin/bash
# ============================================================
# JobGraph - 安装脚本
# ============================================================

set -e

echo "=========================================="
echo "安装 JobGraph"
echo "=========================================="
echo ""

# 获取安装目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="$HOME/JobGraph"

echo "安装目录: $INSTALL_DIR"
echo ""

# 复制文件
echo "[1/3] 复制文件..."
mkdir -p "$INSTALL_DIR"
cp -r "$SCRIPT_DIR/runtime" "$INSTALL_DIR/"
cp -r "$SCRIPT_DIR/app" "$INSTALL_DIR/"
cp -r "$SCRIPT_DIR/bin" "$INSTALL_DIR/"
mkdir -p "$INSTALL_DIR/logs"
mkdir -p "$INSTALL_DIR/pids"
mkdir -p "$INSTALL_DIR/data/redis"
mkdir -p "$INSTALL_DIR/app/data/user"

echo "  文件已复制"

# 安装 Python 依赖
echo "[2/3] 安装 Python 依赖..."
PYTHON="$INSTALL_DIR/runtime/python/install/bin/python3"
cd "$INSTALL_DIR/app"
$PYTHON -m pip install -r requirements.txt -q 2>/dev/null || echo "  部分依赖安装失败，继续..."

echo "  依赖已安装"

# 创建桌面快捷方式
echo "[3/3] 创建快捷方式..."

cat > "$INSTALL_DIR/start.sh" << START_EOF
#!/bin/bash
cd "$INSTALL_DIR"
./bin/start.sh
START_EOF
chmod +x "$INSTALL_DIR/start.sh"

cat > "$INSTALL_DIR/stop.sh" << STOP_EOF
#!/bin/bash
cd "$INSTALL_DIR"
./bin/stop.sh
STOP_EOF
chmod +x "$INSTALL_DIR/stop.sh"

echo "  快捷方式已创建"

# 完成
echo ""
echo "=========================================="
echo "安装完成！"
echo "=========================================="
echo ""
echo "启动 JobGraph:"
echo "  cd $INSTALL_DIR"
echo "  ./start.sh"
echo ""
echo "或直接访问: http://localhost:8504"
echo ""
INSTALL_EOF

chmod +x "$BUILD_DIR/install.sh"

echo "  安装脚本已创建"

# ============================================================
# 创建自解压包
# ============================================================
echo "[5/5] 创建自解压包..."

# 检查 makeself 是否安装
if ! command -v makeself &> /dev/null; then
    echo "安装 makeself..."
    if command -v apt-get &> /dev/null; then
        sudo apt-get install -y makeself
    elif command -v yum &> /dev/null; then
        sudo yum install -y makeself
    else
        echo "错误: 请先安装 makeself"
        echo "  Ubuntu/Debian: sudo apt-get install makeself"
        echo "  CentOS/RHEL: sudo yum install makeself"
        exit 1
    fi
fi

# 创建自解压包
makeself "$BUILD_DIR" "$OUTPUT_DIR/JobGraph-Linux-x64.run" "JobGraph Installer" ./install.sh

echo ""
echo "=========================================="
echo "安装包创建完成！"
echo "=========================================="
echo ""
echo "输出文件: $OUTPUT_DIR/JobGraph-Linux-x64.run"
echo ""
echo "安装方法:"
echo "  chmod +x JobGraph-Linux-x64.run"
echo "  ./JobGraph-Linux-x64.run"
echo ""
