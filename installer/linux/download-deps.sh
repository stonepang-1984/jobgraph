#!/bin/bash
# ============================================================
# JobGraph - Linux 依赖准备脚本
# 使用系统 Python 创建可移植的虚拟环境
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR/../.."
DEPS_DIR="$PROJECT_ROOT/deps/linux"

mkdir -p "$DEPS_DIR"

echo "=========================================="
echo "准备 Linux 依赖"
echo "=========================================="

# ============================================================
# 准备 Python 虚拟环境
# ============================================================
echo ""
echo "[1/3] 准备 Python 虚拟环境..."

VENV_DIR="$DEPS_DIR/python"

if [ -d "$VENV_DIR" ] && [ -f "$VENV_DIR/bin/python3" ]; then
    echo "  Python 环境已存在，跳过"
else
    # 使用系统 Python 创建虚拟环境
    python3 -m venv "$VENV_DIR"
    
    # 升级 pip
    "$VENV_DIR/bin/pip" install --upgrade pip -q
    
    echo "  Python 虚拟环境创建完成"
fi

# ============================================================
# 安装 Python 依赖
# ============================================================
echo ""
echo "[2/3] 安装 Python 依赖..."

REQUIREMENTS="$PROJECT_ROOT/requirements.txt"
if [ -f "$REQUIREMENTS" ]; then
    "$VENV_DIR/bin/pip" install -r "$REQUIREMENTS" -q 2>/dev/null || {
        echo "  部分依赖安装失败，尝试逐个安装..."
        while IFS= read -r dep; do
            [ -z "$dep" ] && continue
            [[ "$dep" == \#* ]] && continue
            "$VENV_DIR/bin/pip" install "$dep" -q 2>/dev/null || echo "  跳过: $dep"
        done < "$REQUIREMENTS"
    }
    echo "  Python 依赖安装完成"
else
    echo "  警告: requirements.txt 不存在"
fi

# ============================================================
# 下载 Neo4j
# ============================================================
echo ""
echo "[3/3] 下载 Neo4j..."

NEO4J_DIR="$DEPS_DIR/neo4j"

if [ -d "$NEO4J_DIR" ] && [ -f "$NEO4J_DIR/bin/neo4j" ]; then
    echo "  Neo4j 已存在，跳过下载"
else
    NEO4J_URL="https://dist.neo4j.org/neo4j-community-5.26.0-unix.tar.gz"
    echo "  下载: $NEO4J_URL"
    curl -L -o /tmp/neo4j.tar.gz "$NEO4J_URL"
    mkdir -p "$DEPS_DIR"
    tar xzf /tmp/neo4j.tar.gz -C "$DEPS_DIR"
    mv "$DEPS_DIR/neo4j-community-5.26.0" "$NEO4J_DIR"
    rm /tmp/neo4j.tar.gz
    echo "  Neo4j 下载完成"
fi

# ============================================================
# Redis 使用系统自带或内嵌
# ============================================================
echo ""
echo "检查 Redis..."
if command -v redis-server &> /dev/null; then
    echo "  Redis 已安装: $(redis-server --version)"
else
    echo "  Redis 未安装，将使用系统包管理器安装"
    # 在构建环境中安装
    sudo apt-get install -y redis-server 2>/dev/null || echo "  Redis 安装失败，用户需自行安装"
fi

echo ""
echo "=========================================="
echo "依赖准备完成！"
echo "=========================================="
echo ""
echo "目录: $DEPS_DIR/"
echo "  ├── python/    Python 虚拟环境"
echo "  └── neo4j/     Neo4j 5.26.0"
echo ""
