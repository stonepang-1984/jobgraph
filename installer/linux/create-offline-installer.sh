#!/bin/bash
# ============================================================
# JobGraph - Linux 离线安装包构建脚本
# 打包所有依赖，用户无需联网即可安装
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
echo "[1/7] 检查依赖..."

if [ ! -d "$DEPS_DIR" ]; then
    echo "错误: 依赖目录不存在"
    echo "请先运行: ./installer/linux/download-deps.sh"
    exit 1
fi

# 检查依赖完整性
MISSING=0
for dep in python neo4j redis; do
    if [ ! -d "$DEPS_DIR/$dep" ]; then
        echo "错误: 缺少 $dep"
        MISSING=1
    fi
done

if [ $MISSING -eq 1 ]; then
    echo "请先下载所有依赖"
    exit 1
fi

echo "  依赖检查通过"

# ============================================================
# 清理构建目录
# ============================================================
echo "[2/7] 清理构建目录..."
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"
mkdir -p "$OUTPUT_DIR"

# ============================================================
# 复制运行时依赖
# ============================================================
echo "[3/7] 复制运行时依赖..."

cp -r "$DEPS_DIR/python" "$BUILD_DIR/runtime/"
cp -r "$DEPS_DIR/neo4j" "$BUILD_DIR/runtime/"
cp -r "$DEPS_DIR/redis" "$BUILD_DIR/runtime/"

# 清理不需要的文件（减小体积）
rm -rf "$BUILD_DIR/runtime/python/test" 2>/dev/null || true
rm -rf "$BUILD_DIR/runtime/python/Doc" 2>/dev/null || true
rm -rf "$BUILD_DIR/runtime/neo4j/logs" 2>/dev/null || true
rm -rf "$BUILD_DIR/runtime/neo4j/data" 2>/dev/null || true

echo "  运行时依赖已复制"

# ============================================================
# 复制 Python 依赖（预编译的 wheel 包）
# ============================================================
echo "[4/7] 准备 Python 依赖..."

PYTHON="$BUILD_DIR/runtime/python/install/bin/python3"
PIP_DIR="$BUILD_DIR/app/lib/python"

mkdir -p "$PIP_DIR"

# 下载所有 Python 依赖到本地
echo "  下载 Python 依赖..."
$PYTHON -m pip download \
    -r "$PROJECT_ROOT/requirements.txt" \
    -d "$PIP_DIR" \
    --platform manylinux2014_x86_64 \
    --python-version 3.11 \
    --only-binary=:all: \
    2>/dev/null || {
        # 如果平台特定下载失败，使用通用下载
        $PYTHON -m pip download \
            -r "$PROJECT_ROOT/requirements.txt" \
            -d "$PIP_DIR" \
            2>/dev/null || echo "  部分依赖下载失败"
    }

echo "  Python 依赖已准备"

# ============================================================
# 复制应用程序
# ============================================================
echo "[5/7] 复制应用程序..."

mkdir -p "$BUILD_DIR/app"
cp -r "$PROJECT_ROOT/src" "$BUILD_DIR/app/"
cp -r "$PROJECT_ROOT/web" "$BUILD_DIR/app/"
cp -r "$PROJECT_ROOT/config" "$BUILD_DIR/app/"
cp -r "$PROJECT_ROOT/scripts" "$BUILD_DIR/app/"
cp -r "$PROJECT_ROOT/data/initial" "$BUILD_DIR/app/data/" 2>/dev/null || mkdir -p "$BUILD_DIR/app/data/initial"
cp -r "$PROJECT_ROOT/api" "$BUILD_DIR/app/"
cp "$PROJECT_ROOT/requirements.txt" "$BUILD_DIR/app/"
cp "$PROJECT_ROOT/pyproject.toml" "$BUILD_DIR/app/"

# 复制启动脚本
mkdir -p "$BUILD_DIR/bin"
cp -r "$PROJECT_ROOT/bin/linux/"* "$BUILD_DIR/bin/"
chmod +x "$BUILD_DIR/bin/"*.sh

echo "  应用程序已复制"

# ============================================================
# 创建离线安装脚本
# ============================================================
echo "[6/7] 创建离线安装脚本..."

cat > "$BUILD_DIR/install.sh" << 'INSTALL_EOF'
#!/bin/bash
# ============================================================
# JobGraph - 离线安装脚本
# ============================================================

set -e

echo "=========================================="
echo "安装 JobGraph (离线版)"
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

# 安装 Python 依赖（离线）
echo "[2/3] 安装 Python 依赖（离线）..."
PYTHON="$INSTALL_DIR/runtime/python/install/bin/python3"
cd "$INSTALL_DIR/app"

# 从本地 wheel 包安装
if [ -d "lib/python" ] && [ "$(ls -A lib/python)" ]; then
    $PYTHON -m pip install --no-index --find-links=lib/python -r requirements.txt -q 2>/dev/null || {
        echo "  部分依赖安装失败，尝试在线安装..."
        $PYTHON -m pip install -r requirements.txt -q 2>/dev/null || echo "  依赖安装失败，请手动安装"
    }
else
    echo "  未找到本地依赖，尝试在线安装..."
    $PYTHON -m pip install -r requirements.txt -q 2>/dev/null || echo "  依赖安装失败，请手动安装"
fi

echo "  依赖已安装"

# 创建快捷方式
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

echo "  离线安装脚本已创建"

# ============================================================
# 创建自解压包
# ============================================================
echo "[7/7] 创建自解压包..."

# 检查 makeself
if ! command -v makeself &> /dev/null; then
    echo "安装 makeself..."
    sudo apt-get install -y makeself 2>/dev/null || sudo yum install -y makeself 2>/dev/null
fi

# 创建自解压包
makeself "$BUILD_DIR" "$OUTPUT_DIR/JobGraph-Linux-x64-Offline.run" "JobGraph Offline Installer" ./install.sh

# 获取文件大小
FILE_SIZE=$(du -h "$OUTPUT_DIR/JobGraph-Linux-x64-Offline.run" | cut -f1)

echo ""
echo "=========================================="
echo "离线安装包创建完成！"
echo "=========================================="
echo ""
echo "输出文件: $OUTPUT_DIR/JobGraph-Linux-x64-Offline.run"
echo "文件大小: $FILE_SIZE"
echo ""
echo "安装方法（无需联网）:"
echo "  chmod +x JobGraph-Linux-x64-Offline.run"
echo "  ./JobGraph-Linux-x64-Offline.run"
echo ""
