#!/bin/bash
# ============================================================
# JobGraph - Linux 安装包构建脚本
# 在线安装：只包含核心代码，安装时下载依赖
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR/../.."
BUILD_DIR="$PROJECT_ROOT/build/linux"
OUTPUT_DIR="$PROJECT_ROOT/dist"

echo "=========================================="
echo "创建 Linux 安装包 (在线版)"
echo "=========================================="

# 清理构建目录
echo "[1/3] 准备构建目录..."
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR" "$OUTPUT_DIR"

# 复制应用程序
echo "[2/3] 复制应用程序..."
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

echo "  应用程序已复制"

# 创建安装脚本
echo "[3/3] 创建安装脚本..."
cat > "$BUILD_DIR/install.sh" << 'INSTALL_EOF'
#!/bin/bash
# ============================================================
# JobGraph - 在线安装脚本
# ============================================================

set -e

echo "=========================================="
echo "JobGraph 安装程序 (在线版)"
echo "=========================================="
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="$HOME/JobGraph"

echo "安装目录: $INSTALL_DIR"
echo ""

# 检查系统依赖
echo "[1/5] 检查系统依赖..."

if ! command -v python3 &> /dev/null; then
    echo "正在安装 Python..."
    if command -v apt-get &> /dev/null; then
        sudo apt-get update && sudo apt-get install -y python3 python3-pip python3-venv
    elif command -v yum &> /dev/null; then
        sudo yum install -y python3 python3-pip
    else
        echo "错误: 请手动安装 Python 3.10+"
        exit 1
    fi
fi
echo "  ✓ Python: $(python3 --version)"

if ! command -v java &> /dev/null; then
    echo "正在安装 Java..."
    if command -v apt-get &> /dev/null; then
        sudo apt-get install -y default-jre
    elif command -v yum &> /dev/null; then
        sudo yum install -y java-11-openjdk
    else
        echo "错误: 请手动安装 Java 11+"
        exit 1
    fi
fi
echo "  ✓ Java: $(java -version 2>&1 | head -1)"

# 复制应用程序
echo ""
echo "[2/5] 复制应用程序..."
mkdir -p "$INSTALL_DIR"
cp -r "$SCRIPT_DIR/app/"* "$INSTALL_DIR/"
mkdir -p "$INSTALL_DIR/logs" "$INSTALL_DIR/pids" "$INSTALL_DIR/data/user"
echo "  应用程序已复制"

# 安装 Python 依赖
echo ""
echo "[3/5] 安装 Python 依赖 (需要几分钟)..."
cd "$INSTALL_DIR"
python3 -m pip install -r requirements.txt -q 2>/dev/null || {
    echo "  部分依赖安装失败，尝试逐个安装..."
    while IFS= read -r dep; do
        [ -z "$dep" ] && continue
        [[ "$dep" == \#* ]] && continue
        python3 -m pip install "$dep" -q 2>/dev/null || echo "  跳过: $dep"
    done < requirements.txt
}
echo "  Python 依赖已安装"

# 安装 Neo4j
echo ""
echo "[4/5] 安装 Neo4j..."
NEO4J_DIR="$INSTALL_DIR/runtime/neo4j"
if [ -d "$NEO4J_DIR" ] && [ -f "$NEO4J_DIR/bin/neo4j" ]; then
    echo "  Neo4j 已存在"
else
    echo "  下载 Neo4j (约 400MB)..."
    mkdir -p "$INSTALL_DIR/runtime"
    curl -L -o /tmp/neo4j.tar.gz "https://dist.neo4j.org/neo4j-community-5.26.0-unix.tar.gz"
    tar xzf /tmp/neo4j.tar.gz -C "$INSTALL_DIR/runtime/"
    mv "$INSTALL_DIR/runtime/neo4j-community-5.26.0" "$NEO4J_DIR"
    rm /tmp/neo4j.tar.gz
    echo "  Neo4j 已安装"
fi

# 创建启动/停止脚本
echo ""
echo "[5/5] 创建启动脚本..."
cat > "$INSTALL_DIR/start.sh" << 'START_EOF'
#!/bin/bash
set -e
INSTALL_DIR="$(cd "$(dirname "$0")" && pwd)"
NEO4J_HOME="$INSTALL_DIR/runtime/neo4j"
LOG_DIR="$INSTALL_DIR/logs"
PID_DIR="$INSTALL_DIR/pids"
mkdir -p "$LOG_DIR" "$PID_DIR"

echo "启动 JobGraph..."

# Redis
if redis-cli -p 6379 ping 2>/dev/null | grep -q "PONG"; then
    echo "Redis 已在运行"
elif command -v redis-server &> /dev/null; then
    redis-server --daemonize yes --logfile "$LOG_DIR/redis.log"
    echo "Redis 已启动"
else
    echo "警告: Redis 未安装"
fi

# Neo4j
export NEO4J_HOME
$NEO4J_HOME/bin/neo4j start > "$LOG_DIR/neo4j.log" 2>&1
echo "Neo4j 启动中..."
for i in {1..30}; do
    python3 -c "from neo4j import GraphDatabase; d=GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'password123')); d.verify_connectivity(); d.close()" 2>/dev/null && break
    [ $i -eq 30 ] && echo "Neo4j 启动超时" && exit 1
    sleep 2
done
echo "Neo4j 已就绪"

# 初始化数据库
cd "$INSTALL_DIR"
python3 scripts/init_neo4j.py 2>/dev/null || true
[ -f "data/initial/admin_data.json" ] && python3 scripts/import_from_admin.py --file data/initial/admin_data.json 2>/dev/null

# 启动 Web 界面
nohup python3 -m streamlit run web/jobgraph.py --server.port 8504 --server.headless true > "$LOG_DIR/streamlit.log" 2>&1 &
echo $! > "$PID_DIR/streamlit.pid"
echo "Web 界面已启动"

echo ""
echo "=========================================="
echo "JobGraph 启动完成！"
echo "访问: http://localhost:8504"
echo "停止: $INSTALL_DIR/stop.sh"
echo "=========================================="
START_EOF
chmod +x "$INSTALL_DIR/start.sh"

cat > "$INSTALL_DIR/stop.sh" << 'STOP_EOF'
#!/bin/bash
INSTALL_DIR="$(cd "$(dirname "$0")" && pwd)"
PID_DIR="$INSTALL_DIR/pids"
NEO4J_HOME="$INSTALL_DIR/runtime/neo4j"
echo "停止 JobGraph..."
[ -f "$PID_DIR/streamlit.pid" ] && kill "$(cat $PID_DIR/streamlit.pid)" 2>/dev/null && echo "Web 界面已停止"
rm -f "$PID_DIR/streamlit.pid"
$NEO4J_HOME/bin/neo4j stop 2>/dev/null || true
redis-cli -p 6379 shutdown 2>/dev/null || true
echo "JobGraph 已停止"
STOP_EOF
chmod +x "$INSTALL_DIR/stop.sh"

echo "  启动脚本已创建"

# 完成
echo ""
echo "=========================================="
echo "安装完成！"
echo "=========================================="
echo "启动: cd $INSTALL_DIR && ./start.sh"
echo "访问: http://localhost:8504"
echo ""
INSTALL_EOF
chmod +x "$BUILD_DIR/install.sh"

# 创建自解压包
if ! command -v makeself &> /dev/null; then
    echo "错误: makeself 未安装"
    exit 1
fi

makeself "$BUILD_DIR" "$OUTPUT_DIR/JobGraph-Linux-x64.run" "JobGraph Installer" ./install.sh

FILE_SIZE=$(du -h "$OUTPUT_DIR/JobGraph-Linux-x64.run" | cut -f1)

echo ""
echo "=========================================="
echo "安装包创建完成！"
echo "=========================================="
echo "文件: $OUTPUT_DIR/JobGraph-Linux-x64.run ($FILE_SIZE)"
echo ""
