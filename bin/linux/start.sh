#!/bin/bash
# ============================================================
# JobGraph - Linux 启动脚本
# ============================================================

set -e

# 获取安装目录
INSTALL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
APP_DIR="$INSTALL_DIR/app"
RUNTIME_DIR="$INSTALL_DIR/runtime"

# 运行时路径
NEO4J_HOME="$RUNTIME_DIR/neo4j"
PYTHON="$RUNTIME_DIR/python/bin/python3"

# 日志目录
LOG_DIR="$INSTALL_DIR/logs"
mkdir -p "$LOG_DIR"

# PID 文件目录
PID_DIR="$INSTALL_DIR/pids"
mkdir -p "$PID_DIR"

echo "=========================================="
echo "启动 JobGraph"
echo "=========================================="
echo "安装目录: $INSTALL_DIR"
echo ""

# ============================================================
# 检查服务是否已运行
# ============================================================
if [ -f "$PID_DIR/neo4j.pid" ] && kill -0 "$(cat $PID_DIR/neo4j.pid)" 2>/dev/null; then
    echo "服务已在运行，如需重启请先执行 stop.sh"
    exit 0
fi

# ============================================================
# 启动 Redis
# ============================================================
echo "[1/4] 启动 Redis..."

if redis-cli -p 6379 ping 2>/dev/null | grep -q "PONG"; then
    echo "  Redis 已在运行"
elif command -v redis-server &> /dev/null; then
    redis-server --daemonize yes --logfile "$LOG_DIR/redis.log"
    echo "  Redis 已启动"
else
    echo "  警告: Redis 未安装，部分功能可能不可用"
fi

# ============================================================
# 启动 Neo4j
# ============================================================
echo "[2/4] 启动 Neo4j..."

export NEO4J_HOME="$NEO4J_HOME"

$NEO4J_HOME/bin/neo4j start > "$LOG_DIR/neo4j.log" 2>&1
echo "  Neo4j 启动中..."

# 等待 Neo4j 就绪
echo "  等待 Neo4j 就绪..."
for i in {1..30}; do
    if $PYTHON -c "from neo4j import GraphDatabase; d=GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'password123')); d.verify_connectivity(); d.close()" 2>/dev/null; then
        echo "  Neo4j 已就绪"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "  Neo4j 启动超时，请检查日志: $LOG_DIR/neo4j.log"
        exit 1
    fi
    sleep 2
done

# ============================================================
# 初始化数据库
# ============================================================
echo "[3/4] 初始化数据库..."

cd "$APP_DIR"
$PYTHON scripts/init_neo4j.py 2>/dev/null || echo "  数据库已初始化"

if [ -f "data/initial/admin_data.json" ]; then
    echo "  导入初始数据..."
    $PYTHON scripts/import_from_admin.py --file data/initial/admin_data.json 2>/dev/null || echo "  数据已导入"
fi

# ============================================================
# 启动 Web 界面
# ============================================================
echo "[4/4] 启动 Web 界面..."

cd "$APP_DIR"
nohup $PYTHON -m streamlit run web/jobgraph.py \
    --server.port 8504 \
    --server.headless true \
    > "$LOG_DIR/streamlit.log" 2>&1 &

STREAMLIT_PID=$!
echo $STREAMLIT_PID > "$PID_DIR/streamlit.pid"
echo "  Web 界面已启动 (PID: $STREAMLIT_PID)"

# ============================================================
# 完成
# ============================================================
echo ""
echo "=========================================="
echo "JobGraph 启动完成！"
echo "=========================================="
echo ""
echo "访问: http://localhost:8504"
echo "停止: $INSTALL_DIR/bin/stop.sh"
echo ""
