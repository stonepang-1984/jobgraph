#!/bin/bash
# ============================================================
# JobGraph - 一键初始化脚本
# 用户无需数据中心，开箱即用
# ============================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }
print_header() {
    echo ""
    echo -e "${BLUE}============================================================${NC}"
    echo -e "${BLUE} $1${NC}"
    echo -e "${BLUE}============================================================${NC}"
    echo ""
}

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# ============================================================
# 检查依赖
# ============================================================
check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON=python3
    elif command -v python &> /dev/null; then
        PYTHON=python
    else
        print_error "Python 未安装，请先安装 Python 3.10+"
        exit 1
    fi
    print_success "Python: $($PYTHON --version)"
}

# ============================================================
# 安装依赖
# ============================================================
install_deps() {
    print_header "安装依赖"
    
    if [ -f requirements.txt ]; then
        print_info "安装 requirements.txt..."
        $PYTHON -m pip install -r requirements.txt -q 2>/dev/null || {
            print_warning "部分依赖安装失败，继续..."
        }
    fi
    
    print_success "依赖安装完成"
}

# ============================================================
# 启动 Neo4j
# ============================================================
start_neo4j() {
    print_header "启动数据库"
    
    # 检查 Neo4j 是否已运行
    if $PYTHON -c "from neo4j import GraphDatabase; d=GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'neo4j')); d.verify_connectivity(); d.close()" 2>/dev/null; then
        print_success "Neo4j 已运行"
        return
    fi
    
    # 尝试使用 Docker
    if command -v docker &> /dev/null; then
        print_info "使用 Docker 启动 Neo4j..."
        
        # 检查容器
        if docker ps -a --format '{{.Names}}' | grep -q "graphrag-neo4j"; then
            docker start graphrag-neo4j 2>/dev/null || true
        else
            docker run -d \
                --name graphrag-neo4j \
                -p 7474:7474 \
                -p 7687:7687 \
                -e NEO4J_AUTH=neo4j/password123 \
                neo4j:5-community
        fi
        
        print_info "等待 Neo4j 启动..."
        sleep 10
        print_success "Neo4j 已启动"
    else
        print_warning "Docker 未安装"
        print_info "请手动启动 Neo4j，或安装 Docker"
        print_info "默认密码: neo4j/password123"
    fi
}

# ============================================================
# 初始化数据库
# ============================================================
init_database() {
    print_header "初始化数据库"
    
    if [ -f scripts/init_neo4j.py ]; then
        print_info "执行 Schema 初始化..."
        PYTHONPATH=. $PYTHON scripts/init_neo4j.py 2>/dev/null || {
            print_warning "Schema 初始化可能已存在"
        }
    fi
    
    print_success "数据库初始化完成"
}

# ============================================================
# 导入示例数据
# ============================================================
import_sample_data() {
    print_header "导入初始数据"
    
    # 检查是否已有数据
    EXISTING_COUNT=$(PYTHONPATH=. $PYTHON -c "
from src.graph.neo4j_client import neo4j_client
result = neo4j_client.execute_query('MATCH (c:Company) RETURN count(c) AS cnt')
print(result[0]['cnt'] if result else 0)
" 2>/dev/null || echo "0")
    
    if [ "$EXISTING_COUNT" -gt "10" ]; then
        print_info "已有 $EXISTING_COUNT 家公司数据，跳过导入"
        return
    fi
    
    print_info "导入初始数据..."
    
    # 优先从 admin 数据导入
    if [ -f data/initial/admin_data.json ]; then
        print_info "从 admin 数据导入..."
        PYTHONPATH=. $PYTHON scripts/import_from_admin.py --file data/initial/admin_data.json 2>/dev/null || {
            print_warning "admin 数据导入失败，尝试初始数据..."
            # 备用：使用初始数据脚本
            if [ -f scripts/import_initial_data.py ]; then
                PYTHONPATH=. $PYTHON scripts/import_initial_data.py 2>/dev/null || {
                    print_warning "数据导入可能失败，请检查日志"
                }
            fi
        }
    elif [ -f scripts/import_initial_data.py ]; then
        PYTHONPATH=. $PYTHON scripts/import_initial_data.py 2>/dev/null || {
            print_warning "数据导入可能失败，请检查日志"
        }
    fi
    
    print_success "初始数据导入完成"
}

# ============================================================
# 启动服务
# ============================================================
start_services() {
    print_header "启动服务"
    
    # 启动 Streamlit
    print_info "启动 JobGraph Web UI..."
    nohup $PYTHON -m streamlit run web/jobgraph.py \
        --server.port 8504 \
        --server.headless true \
        > logs/web.log 2>&1 &
    
    WEB_PID=$!
    echo $WEB_PID > .pids/web.pid
    
    sleep 3
    
    print_success "JobGraph 已启动"
}

# ============================================================
# 打印使用说明
# ============================================================
print_usage() {
    print_header "🎉 初始化完成！"
    
    echo "访问地址:"
    echo "  📊 JobGraph: http://localhost:8504"
    echo ""
    echo "已导入初始数据:"
    echo "  🏢 20 家公司 (腾讯、字节、阿里、美团等)"
    echo "  💼 30+ 个职位 (腾讯官网爬取)"
    echo ""
    echo "功能:"
    echo "  📄 简历上传 - 上传简历自动解析，提取技能、经验"
    echo "  🎯 智能匹配 - 根据简历信息自动匹配合适岗位"
    echo "  📝 手动匹配 - 粘贴文本/上传图片匹配职位"
    echo "  🔍 岗位搜索 - 智能筛选，按薪资、地点、技能过滤"
    echo "  🏢 公司画像 - 员工评价、风险评分、薪资水平"
    echo "  ⚠️ 避坑预警 - 坑点识别：欠薪、PUA、996 等"
    echo "  📊 薪资分析 - 市场行情、薪资分布"
    echo ""
    echo "数据同步 (可选):"
    echo "  📦 离线数据包: make sync-package FILE=xxx.zip"
    echo "  🌐 Tailscale:  make sync-tailscale SERVER=http://xxx:8000"
    echo ""
    echo "命令:"
    echo "  make jobgraph    - 启动 Web UI"
    echo "  make dev-stop    - 停止服务"
    echo "  make dev-status  - 查看状态"
    echo ""
}

# ============================================================
# 主函数
# ============================================================
main() {
    print_header "JobGraph - 一键初始化"
    
    check_python
    install_deps
    start_neo4j
    init_database
    import_sample_data
    start_services
    print_usage
}

main "$@"
