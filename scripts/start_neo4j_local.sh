#!/bin/bash
# ============================================================
# 启动本地 Neo4j (无需 Docker)
# ============================================================

set -e

# 颜色
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }

# 项目目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
NEO4J_DIR="$PROJECT_ROOT/.neo4j"
NEO4J_VERSION="5.26.0"
NEO4J_EDITION="community"

# Neo4j 目录
mkdir -p "$NEO4J_DIR"

# 检查是否已下载
if [ ! -d "$NEO4J_DIR/neo4j" ]; then
    print_info "下载 Neo4j $NEO4J_VERSION..."
    
    DOWNLOAD_URL="https://dist.neo4j.org/neo4j-community-$NEO4J_VERSION-unix.tar.gz"
    TAR_FILE="$NEO4J_DIR/neo4j.tar.gz"
    
    # 下载
    if command -v wget &> /dev/null; then
        wget -q --show-progress -O "$TAR_FILE" "$DOWNLOAD_URL"
    elif command -v curl &> /dev/null; then
        curl -L -o "$TAR_FILE" "$DOWNLOAD_URL"
    else
        echo "错误: 需要 wget 或 curl"
        exit 1
    fi
    
    # 解压
    print_info "解压 Neo4j..."
    cd "$NEO4J_DIR"
    tar -xzf neo4j.tar.gz
    mv neo4j-community-$NEO4J_VERSION neo4j
    rm neo4j.tar.gz
    cd "$SCRIPT_DIR"
    
    print_success "Neo4j 下载完成"
fi

# 配置 Neo4j
NEO4J_HOME="$NEO4J_DIR/neo4j"

# 修改配置允许远程访问
if ! grep -q "server.default_listen_address=0.0.0.0" "$NEO4J_HOME/conf/neo4j.conf" 2>/dev/null; then
    echo "server.default_listen_address=0.0.0.0" >> "$NEO4J_HOME/conf/neo4j.conf"
fi

# 设置初始密码
export NEO4J_AUTH=neo4j/password123

# 检查是否已运行
if "$NEO4J_HOME/bin/neo4j" status &>/dev/null; then
    print_info "Neo4j 已在运行"
else
    print_info "启动 Neo4j..."
    "$NEO4J_HOME/bin/neo4j" start
    
    # 等待启动
    print_info "等待 Neo4j 就绪..."
    for i in {1..30}; do
        if "$NEO4J_HOME/bin/neo4j" status &>/dev/null; then
            print_success "Neo4j 已启动"
            break
        fi
        sleep 2
        echo -n "."
    done
    echo ""
fi

print_success "Neo4j 准备就绪"
echo ""
echo "Neo4j Web UI: http://localhost:7474"
echo "Bolt 地址: bolt://localhost:7687"
echo "用户名: neo4j"
echo "密码: password123"
echo ""
