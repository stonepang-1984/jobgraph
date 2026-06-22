#!/bin/bash
# ============================================================
# JobGraph - Linux 依赖下载脚本
# 下载 Python、Neo4j、Redis 的 Linux 版本
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

# Python 版本
PYTHON_VERSION="3.11.9"
PYTHON_DIR="python"

# Neo4j 版本
NEO4J_VERSION="5.26.0"
NEO4J_DIR="neo4j"

# Redis 版本
REDIS_VERSION="7.2.4"
REDIS_DIR="redis"

# ============================================================
# 下载 Python
# ============================================================
echo ""
echo "[1/3] 下载 Python ${PYTHON_VERSION}..."

if [ -d "$PYTHON_DIR" ]; then
    echo "  Python 已存在，跳过下载"
else
    PYTHON_URL="https://www.python.org/ftp/python/${PYTHON_VERSION}/Python-${PYTHON_VERSION}.tgz"
    echo "  下载: $PYTHON_URL"
    curl -L -o python.tgz "$PYTHON_URL"
    tar xzf python.tgz
    mv "Python-${PYTHON_VERSION}" "$PYTHON_DIR"
    rm python.tgz
    
    # 编译安装
    cd "$PYTHON_DIR"
    ./configure --prefix="$(pwd)/install" --enable-optimizations
    make -j$(nproc)
    make install
    cd ..
    
    echo "  Python 下载完成"
fi

# ============================================================
# 下载 Neo4j
# ============================================================
echo ""
echo "[2/3] 下载 Neo4j ${NEO4J_VERSION}..."

if [ -d "$NEO4J_DIR" ]; then
    echo "  Neo4j 已存在，跳过下载"
else
    NEO4J_URL="https://dist.neo4j.org/neo4j-community-${NEO4J_VERSION}-unix.tar.gz"
    echo "  下载: $NEO4J_URL"
    curl -L -o neo4j.tar.gz "$NEO4J_URL"
    tar xzf neo4j.tar.gz
    mv "neo4j-community-${NEO4J_VERSION}" "$NEO4J_DIR"
    rm neo4j.tar.gz
    
    echo "  Neo4j 下载完成"
fi

# ============================================================
# 下载 Redis
# ============================================================
echo ""
echo "[3/3] 下载 Redis ${REDIS_VERSION}..."

if [ -d "$REDIS_DIR" ]; then
    echo "  Redis 已存在，跳过下载"
else
    REDIS_URL="https://download.redis.io/releases/redis-${REDIS_VERSION}.tar.gz"
    echo "  下载: $REDIS_URL"
    curl -L -o redis.tar.gz "$REDIS_URL"
    tar xzf redis.tar.gz
    mv "redis-${REDIS_VERSION}" "$REDIS_DIR"
    rm redis.tar.gz
    
    # 编译
    cd "$REDIS_DIR"
    make -j$(nproc)
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
echo "  ├── python/    Python ${PYTHON_VERSION}"
echo "  ├── neo4j/     Neo4j ${NEO4J_VERSION}"
echo "  └── redis/     Redis ${REDIS_VERSION}"
echo ""
