#!/bin/bash
# ============================================================
# Multimodal Graph RAG - 一键部署脚本
# ============================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo ""
    echo -e "${BLUE}============================================================${NC}"
    echo -e "${BLUE} $1${NC}"
    echo -e "${BLUE}============================================================${NC}"
    echo ""
}

# 检查依赖
check_dependencies() {
    print_header "检查依赖"
    
    # 检查 Docker
    if command -v docker &> /dev/null; then
        print_success "Docker 已安装: $(docker --version)"
    else
        print_error "Docker 未安装，请先安装 Docker"
        exit 1
    fi
    
    # 检查 Docker Compose
    if command -v docker-compose &> /dev/null; then
        print_success "Docker Compose 已安装: $(docker-compose --version)"
    elif docker compose version &> /dev/null; then
        print_success "Docker Compose (plugin) 已安装"
        # 创建 docker-compose 别名
        alias docker-compose='docker compose'
    else
        print_error "Docker Compose 未安装，请先安装 Docker Compose"
        exit 1
    fi
    
    # 检查 Python
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version 2>&1)
        print_success "Python 已安装: $PYTHON_VERSION"
    else
        print_warning "Python 未安装，将跳过依赖安装"
    fi
    
    # 检查 pip
    if command -v pip3 &> /dev/null; then
        print_success "pip 已安装"
    elif command -v pip &> /dev/null; then
        print_success "pip 已安装"
    else
        print_warning "pip 未安装，将跳过依赖安装"
    fi
}

# 创建环境变量文件
setup_env() {
    print_header "配置环境变量"
    
    if [ -f .env ]; then
        print_info ".env 文件已存在，跳过创建"
    else
        if [ -f .env.example ]; then
            cp .env.example .env
            print_success "已从 .env.example 创建 .env 文件"
            print_warning "请编辑 .env 文件配置以下必要参数:"
            echo "  - OPENAI_API_KEY: OpenAI API 密钥"
            echo "  - NEO4J_PASSWORD: Neo4j 数据库密码"
        else
            print_error ".env.example 文件不存在"
            exit 1
        fi
    fi
}

# 启动 Docker 服务
start_services() {
    print_header "启动 Docker 服务"
    
    # 停止旧容器
    print_info "停止旧容器..."
    docker-compose down 2>/dev/null || true
    
    # 启动服务
    print_info "启动 Neo4j 和 Redis..."
    docker-compose up -d
    
    # 等待服务启动
    print_info "等待服务启动..."
    sleep 10
    
    # 检查服务状态
    if docker-compose ps | grep -q "Up"; then
        print_success "服务启动成功"
    else
        print_error "服务启动失败，请检查日志: docker-compose logs"
        exit 1
    fi
    
    # 等待 Neo4j 就绪
    print_info "等待 Neo4j 就绪..."
    for i in {1..30}; do
        if docker-compose exec -T neo4j neo4j status &>/dev/null; then
            print_success "Neo4j 已就绪"
            break
        fi
        if [ $i -eq 30 ]; then
            print_warning "Neo4j 启动超时，继续执行..."
        fi
        sleep 2
    done
}

# 安装 Python 依赖
install_dependencies() {
    print_header "安装 Python 依赖"
    
    if command -v pip3 &> /dev/null; then
        PIP=pip3
    elif command -v pip &> /dev/null; then
        PIP=pip
    else
        print_warning "pip 未安装，跳过依赖安装"
        return
    fi
    
    print_info "安装项目依赖..."
    $PIP install -e . 2>/dev/null || $PIP install -r requirements.txt 2>/dev/null || {
        print_warning "依赖安装失败，请手动安装: pip install -e ."
    }
    
    print_success "依赖安装完成"
}

# 初始化数据库
init_database() {
    print_header "初始化数据库"
    
    if command -v python3 &> /dev/null; then
        print_info "执行 Schema 初始化..."
        python3 scripts/init_neo4j.py || {
            print_warning "Schema 初始化失败，请手动执行: python scripts/init_neo4j.py"
        }
    else
        print_warning "Python 未安装，请手动执行: python scripts/init_neo4j.py"
    fi
}

# 验证部署
verify_deployment() {
    print_header "验证部署"
    
    # 检查 Neo4j
    print_info "检查 Neo4j 连接..."
    if curl -s http://localhost:7474 &>/dev/null; then
        print_success "Neo4j Web UI 可访问: http://localhost:7474"
    else
        print_warning "Neo4j Web UI 不可访问"
    fi
    
    # 检查 Redis
    print_info "检查 Redis 连接..."
    if docker-compose exec -T redis redis-cli ping &>/dev/null; then
        print_success "Redis 连接正常"
    else
        print_warning "Redis 连接失败"
    fi
}

# 打印使用说明
print_usage() {
    print_header "部署完成"
    
    echo -e "${GREEN}🎉 Multimodal Graph RAG 部署成功！${NC}"
    echo ""
    echo "服务访问地址:"
    echo "  - Neo4j Web UI: http://localhost:7474"
    echo "  - Neo4j Bolt:   bolt://localhost:7687"
    echo "  - Redis:        localhost:6379"
    echo ""
    echo "常用命令:"
    echo "  make api          - 启动 API 服务 (http://localhost:8000)"
    echo "  make web          - 启动 Web UI (http://localhost:8501)"
    echo "  make ingest FILE= - 摄入文档"
    echo "  make query Q=     - 查询知识图谱"
    echo "  make benchmark    - 运行性能测试"
    echo "  make stop         - 停止服务"
    echo "  make logs         - 查看日志"
    echo ""
    echo "快速开始:"
    echo "  1. 编辑 .env 文件配置 OPENAI_API_KEY"
    echo "  2. 运行 make ingest FILE=your_document.pdf"
    echo "  3. 运行 make query Q=\"你的问题\""
    echo ""
}

# 主函数
main() {
    print_header "Multimodal Graph RAG - 一键部署"
    
    # 解析参数
    SKIP_DEPS=false
    SKIP_DB=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-deps)
                SKIP_DEPS=true
                shift
                ;;
            --skip-db)
                SKIP_DB=true
                shift
                ;;
            --help)
                echo "用法: ./deploy.sh [选项]"
                echo ""
                echo "选项:"
                echo "  --skip-deps  跳过安装 Python 依赖"
                echo "  --skip-db    跳过数据库初始化"
                echo "  --help       显示帮助信息"
                exit 0
                ;;
            *)
                print_error "未知选项: $1"
                exit 1
                ;;
        esac
    done
    
    # 执行部署步骤
    check_dependencies
    setup_env
    start_services
    
    if [ "$SKIP_DEPS" = false ]; then
        install_dependencies
    fi
    
    if [ "$SKIP_DB" = false ]; then
        init_database
    fi
    
    verify_deployment
    print_usage
}

# 执行主函数
main "$@"
