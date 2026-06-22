#!/bin/bash
# ============================================================
# JobGraph - Linux 离线安装包构建脚本
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR/../.."
BUILD_DIR="$PROJECT_ROOT/build/linux-offline"
OUTPUT_DIR="$PROJECT_ROOT/dist"
DEPS_DIR="$PROJECT_ROOT/deps/linux"

echo "=========================================="
echo "构建 Linux 离线安装包"
echo "=========================================="

# ============================================================
# 检查依赖
# ============================================================
echo "[1/6] 检查依赖..."

if [ ! -d "$DEPS_DIR/python" ]; then
    echo "错误: Python 环境不存在"
    echo "请先运行: ./installer/linux/download-deps.sh"
    exit 1
fi

if [ ! -d "$DEPS_DIR/neo4j" ]; then
    echo "错误: Neo4j 未下载"
    exit 1
fi

echo "  依赖检查通过"

# ============================================================
# 清理构建目录
# ============================================================
echo "[2/6] 清理构建目录..."
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"
mkdir -p "$OUTPUT_DIR"

# ============================================================
# 复制运行时依赖
# ============================================================
echo "[3/6] 复制运行时依赖..."

cp -r "$DEPS_DIR/python" "$BUILD_DIR/runtime/"
cp -r "$DEPS_DIR/neo4j" "$BUILD_DIR/runtime/"

rm -rf "$BUILD_DIR/runtime/python/__pycache__" 2>/dev/null || true
rm -rf "$BUILD_DIR/runtime/neo4j/logs" 2>/dev/null || true
rm -rf "$BUILD_DIR/runtime/neo4j/data" 2>/dev/null || true

echo "  运行时依赖已复制"

# ============================================================
# 复制应用程序
# ============================================================
echo "[4/6] 复制应用程序..."

mkdir -p "$BUILD_DIR/app"
cp -r "$PROJECT_ROOT/src" "$BUILD_DIR/app/"
cp -r "$PROJECT_ROOT/web" "$BUILD_DIR/app/"
cp -r "$PROJECT_ROOT/config" "$BUILD_DIR/app/"
cp -r "$PROJECT_ROOT/scripts" "$BUILD_DIR/app/"
cp -r "$PROJECT_ROOT/api" "$BUILD_DIR/app/"
cp "$PROJECT_ROOT/requirements.txt" "$BUILD_DIR/app/"
cp "$PROJECT_ROOT/pyproject.toml" "$BUILD_DIR/app/"

if [ -d "$PROJECT_ROOT/data/initial" ]; then
    mkdir -p "$BUILD_DIR/app/data/initial"
    cp -r "$PROJECT_ROOT/data/initial/"* "$BUILD_DIR/app/data/initial/"
fi

mkdir -p "$BUILD_DIR/bin"
cp "$PROJECT_ROOT/bin/linux/start.sh" "$BUILD_DIR/bin/"
cp "$PROJECT_ROOT/bin/linux/stop.sh" "$BUILD_DIR/bin/"
chmod +x "$BUILD_DIR/bin/"*.sh

echo "  应用程序已复制"

# ============================================================
# 创建安装脚本
# ============================================================
echo "[5/6] 创建安装脚本..."

cat > "$BUILD_DIR/install.sh" << 'INSTALL_EOF'
#!/bin/bash
set -e

echo "=========================================="
echo "安装 JobGraph (离线版)"
echo "=========================================="
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="$HOME/JobGraph"

echo "安装目录: $INSTALL_DIR"
echo ""

echo "[1/2] 复制文件..."
mkdir -p "$INSTALL_DIR"
cp -r "$SCRIPT_DIR/runtime" "$INSTALL_DIR/"
cp -r "$SCRIPT_DIR/app" "$INSTALL_DIR/"
cp -r "$SCRIPT_DIR/bin" "$INSTALL_DIR/"
mkdir -p "$INSTALL_DIR/logs"
mkdir -p "$INSTALL_DIR/pids"
mkdir -p "$INSTALL_DIR/app/data/user"
chmod +x "$INSTALL_DIR/bin/"*.sh
echo "  文件已复制"

echo "[2/2] 创建快捷方式..."
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

echo ""
echo "=========================================="
echo "安装完成！"
echo "=========================================="
echo ""
echo "启动: cd $INSTALL_DIR && ./start.sh"
echo "访问: http://localhost:8504"
echo ""
INSTALL_EOF

chmod +x "$BUILD_DIR/install.sh"

# ============================================================
# 创建自解压包
# ============================================================
echo "[6/6] 创建自解压包..."

if ! command -v makeself &> /dev/null; then
    echo "错误: makeself 未安装"
    exit 1
fi

makeself "$BUILD_DIR" "$OUTPUT_DIR/JobGraph-Linux-x64-Offline.run" "JobGraph Offline Installer" ./install.sh

FILE_SIZE=$(du -h "$OUTPUT_DIR/JobGraph-Linux-x64-Offline.run" | cut -f1)

echo ""
echo "=========================================="
echo "离线安装包创建完成！"
echo "=========================================="
echo "文件: $OUTPUT_DIR/JobGraph-Linux-x64-Offline.run ($FILE_SIZE)"
echo ""
