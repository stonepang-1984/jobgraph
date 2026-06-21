#!/bin/bash
# ============================================================
# JobGraph - Linux 停止脚本
# ============================================================

set -e

# 获取安装目录
INSTALL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
RUNTIME_DIR="$INSTALL_DIR/runtime"
PID_DIR="$INSTALL_DIR/pids"

NEO4J_HOME="$RUNTIME_DIR/neo4j"

echo "=========================================="
echo "停止 JobGraph"
echo "=========================================="
echo ""

# ============================================================
# 停止 Web 界面
# ============================================================
echo "[1/3] 停止 Web 界面..."

if [ -f "$PID_DIR/streamlit.pid" ]; then
    PID=$(cat "$PID_DIR/streamlit.pid")
    if kill -0 "$PID" 2>/dev/null; then
        kill "$PID"
        echo "  Web 界面已停止 (PID: $PID)"
    else
        echo "  Web 界面未运行"
    fi
    rm -f "$PID_DIR/streamlit.pid"
else
    echo "  Web 界面未运行"
fi

# ============================================================
# 停止 Neo4j
# ============================================================
echo "[2/3] 停止 Neo4j..."

if [ -f "$PID_DIR/neo4j.pid" ]; then
    PID=$(cat "$PID_DIR/neo4j.pid")
    if kill -0 "$PID" 2>/dev/null; then
        kill "$PID"
        echo "  Neo4j 已停止 (PID: $PID)"
    else
        echo "  Neo4j 未运行"
    fi
    rm -f "$PID_DIR/neo4j.pid"
else
    echo "  Neo4j 未运行"
fi

# ============================================================
# 停止 Redis
# ============================================================
echo "[3/3] 停止 Redis..."

if redis-cli -p 6379 ping 2>/dev/null | grep -q "PONG"; then
    redis-cli -p 6379 shutdown
    echo "  Redis 已停止"
else
    echo "  Redis 未运行"
fi

# ============================================================
# 完成
# ============================================================
echo ""
echo "=========================================="
echo "JobGraph 已停止"
echo "=========================================="
echo ""
