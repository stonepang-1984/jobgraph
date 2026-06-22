#!/bin/bash
# ============================================================
# JobGraph - Linux 依赖下载脚本
# 下载 Python、Neo4j、Redis 的 Linux 版本（预编译包）
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR/../.."
DEPS_DIR="$PROJECT_ROOT/deps/linux"

mkdir -p "$DEPS_DIR"
cd "$DEPS_DIR"

echo "=========================================="
echo "下载 Linux 依赖"
echo "=========================================="

# ============================================================
# 下载 Python (预编译)
# ============================================================
echo ""
echo "[1/3] 下载 Python..."

if [ -d "python" ] && [ -f "python/bin/python3" ]; then
    echo "  Python 已存在，跳过下载"
else
    # 使用 Conda 的预编译 Python
    PYTHON_URL="https://github.com/indygreg/python-build-standalone/releases/download/20240415/cpython-3.11.9+20240415-x86_64-unknown-linux-gnu-install_only_stripped.tar.gz"
    echo "  下载: $PYTHON_URL"
    curl -L -o python.tar.gz "$PYTHON_URL"
    mkdir -p python
    tar xzf python.tar.gz -C python --strip-components=1
    rm python.tar.gz
    echo "  Python 下载完成"
fi

# ============================================================
# 下载 Neo4j
# ============================================================
echo ""
echo "[2/3] 下载 Neo4j..."

if [ -d "neo4j" ] && [ -f "neo4j/bin/neo4j" ]; then
    echo "  Neo4j 已存在，跳过下载"
else
    NEO4J_URL="https://dist.neo4j.org/neo4j-community-5.26.0-unix.tar.gz"
    echo "  下载: $NEO4J_URL"
    curl -L -o neo4j.tar.gz "$NEO4J_URL"
    tar xzf neo4j.tar.gz
    mv neo4j-community-5.26.0 neo4j
    rm neo4j.tar.gz
    echo "  Neo4j 下载完成"
fi

# ============================================================
# 下载 Redis (预编译)
# ============================================================
echo ""
echo "[3/3] 下载 Redis..."

if [ -d "redis" ] && [ -f "redis/src/redis-server" ]; then
    echo "  Redis 已存在，跳过下载"
else
    # 使用预编译的 Redis
    REDIS_URL="https://download.redis.io/releases/redis-7.2.4.tar.gz"
    echo "  下载: $REDIS_URL"
    curl -L -o redis.tar.gz "$REDIS_URL"
    tar xzf redis.tar.gz
    mv redis-7.2.4 redis
    rm redis.tar.gz
    
    # 编译 Redis（很快）
    cd redis
    make -j$(nproc) 2>/dev/null || make
    cd ..
    
    echo "  Redis 下载完成"
fi

echo ""
echo "=========================================="
echo "所有依赖下载完成！"
echo "=========================================="
echo ""
echo "目录结构:"
echo "  $DEPS_DIR/"
echo "  ├── python/"
echo "  ├── neo4j/"
echo "  └── redis/"
echo ""
