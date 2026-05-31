#!/bin/bash
# ============================================================
# Multimodal Graph RAG - 本地调试启动脚本
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

# PID 文件目录
PID_DIR="$PROJECT_ROOT/.pids"
mkdir -p "$PID_DIR"

# 日志目录
LOG_DIR="$PROJECT_ROOT/logs"
mkdir -p "$LOG_DIR"

# ============================================================
# 检查依赖
# ============================================================
check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON=python3
    elif command -v python &> /dev/null; then
        PYTHON=python
    else
        print_error "Python 未安装"
        exit 1
    fi
    print_success "Python: $($PYTHON --version)"
}

check_pip() {
    if command -v pip3 &> /dev/null; then
        PIP=pip3
    elif command -v pip &> /dev/null; then
        PIP=pip
    else
        print_error "pip 未安装"
        exit 1
    fi
}

# ============================================================
# 检查/启动 Neo4j
# ============================================================
check_docker() {
    if command -v docker &> /dev/null; then
        return 0
    fi
    return 1
}

start_neo4j() {
    print_info "启动 Neo4j..."
    
    # 方案1: 尝试使用 Docker
    if check_docker; then
        # 检查容器是否已存在
        if docker ps -a --format '{{.Names}}' | grep -q "graphrag-neo4j"; then
            if docker ps --format '{{.Names}}' | grep -q "graphrag-neo4j"; then
                print_info "Neo4j 容器已在运行"
            else
                docker start graphrag-neo4j
                print_info "启动已存在的 Neo4j 容器"
            fi
        else
            docker run -d \
                --name graphrag-neo4j \
                -p 7474:7474 \
                -p 7687:7687 \
                -e NEO4J_AUTH=neo4j/password123 \
                -e NEO4J_PLUGINS='["apoc"]' \
                -v neo4j_data:/data \
                neo4j:5-community
            print_info "创建并启动 Neo4j 容器"
        fi
        
        print_info "等待 Neo4j 启动..."
        for i in {1..30}; do
            if docker exec graphrag-neo4j neo4j status &>/dev/null 2>&1; then
                print_success "Neo4j 已启动"
                return 0
            fi
            sleep 2
            echo -n "."
        done
        echo ""
        return 0
    fi
    
    # 方案2: 检查本地 Neo4j
    if command -v neo4j &> /dev/null; then
        print_info "使用本地 Neo4j..."
        neo4j start
        sleep 5
        print_success "本地 Neo4j 已启动"
        return 0
    fi
    
    # 方案3: 提示用户
    print_error "无法启动 Neo4j"
    echo ""
    echo "请选择以下方式之一安装 Neo4j:"
    echo ""
    echo "方式1: 安装 Docker (推荐)"
    echo "  curl -fsSL https://get.docker.com | sh"
    echo "  sudo usermod -aG docker \$USER"
    echo "  # 重新登录后运行: ./dev.sh"
    echo ""
    echo "方式2: 直接安装 Neo4j"
    echo "  # Ubuntu/Debian:"
    echo "  wget -O - https://debian.neo4j.com/neotechnology.gpg.key | sudo apt-key add -"
    echo "  echo 'deb https://debian.neo4j.com stable latest' | sudo tee /etc/apt/sources.list.d/neo4j.list"
    echo "  sudo apt update && sudo apt install neo4j"
    echo "  sudo systemctl start neo4j"
    echo ""
    echo "方式3: 使用 Docker 手动启动"
    echo "  docker run -d --name graphrag-neo4j \\"
    echo "    -p 7474:7474 -p 7687:7687 \\"
    echo "    -e NEO4J_AUTH=neo4j/password123 \\"
    echo "    neo4j:5-community"
    echo ""
    exit 1
}

start_redis() {
    print_info "启动 Redis..."
    
    # 方案1: 尝试使用 Docker
    if check_docker; then
        if docker ps -a --format '{{.Names}}' | grep -q "graphrag-redis"; then
            if docker ps --format '{{.Names}}' | grep -q "graphrag-redis"; then
                print_info "Redis 容器已在运行"
            else
                docker start graphrag-redis
                print_info "启动已存在的 Redis 容器"
            fi
        else
            docker run -d --name graphrag-redis -p 6379:6379 redis:7-alpine
            print_info "创建并启动 Redis 容器"
        fi
        sleep 2
        print_success "Redis 已启动"
        return 0
    fi
    
    # 方案2: 检查本地 Redis
    if command -v redis-server &> /dev/null; then
        print_info "使用本地 Redis..."
        redis-server --daemonize yes
        print_success "本地 Redis 已启动"
        return 0
    fi
    
    print_warning "Redis 未安装 (可选，不影响核心功能)"
}

check_neo4j() {
    print_info "检查 Neo4j 连接..."
    
    # 从 .env 读取配置
    if [ -f .env ]; then
        source .env
    fi
    
    NEO4J_URI=${NEO4J_URI:-"bolt://localhost:7687"}
    NEO4J_USER=${NEO4J_USERNAME:-"neo4j"}
    NEO4J_PASS=${NEO4J_PASSWORD:-"password123"}
    
    # 尝试连接
    $PYTHON -c "
from neo4j import GraphDatabase
try:
    driver = GraphDatabase.driver('$NEO4J_URI', auth=('$NEO4J_USER', '$NEO4J_PASS'))
    driver.verify_connectivity()
    driver.close()
    print('OK')
except Exception as e:
    print(f'FAIL: {e}')
    exit(1)
" 2>/dev/null

    if [ $? -eq 0 ]; then
        print_success "Neo4j 连接成功: $NEO4J_URI"
    else
        print_warning "Neo4j 未运行，正在自动启动..."
        start_neo4j
        
        # 再次检查连接
        $PYTHON -c "
from neo4j import GraphDatabase
try:
    driver = GraphDatabase.driver('$NEO4J_URI', auth=('$NEO4J_USER', '$NEO4J_PASS'))
    driver.verify_connectivity()
    driver.close()
    print('OK')
except Exception as e:
    print(f'FAIL: {e}')
    exit(1)
" 2>/dev/null

        if [ $? -eq 0 ]; then
            print_success "Neo4j 连接成功"
        else
            print_error "Neo4j 连接失败，请检查 Docker 是否正常运行"
            exit 1
        fi
    fi
}

check_redis_optional() {
    print_info "检查 Redis (可选)..."
    
    # 检查 redis-cli
    if command -v redis-cli &> /dev/null; then
        if redis-cli ping &>/dev/null; then
            print_success "Redis 连接成功"
            return
        fi
    fi
    
    # 尝试使用 Docker 启动 Redis
    print_warning "Redis 未运行，正在自动启动..."
    start_redis
}

# ============================================================
# 安装依赖
# ============================================================
install_deps() {
    print_header "安装 Python 依赖"
    
    check_pip
    
    if [ -f requirements.txt ]; then
        print_info "安装 requirements.txt..."
        $PIP install -r requirements.txt -q
        print_success "依赖安装完成"
    else
        print_warning "requirements.txt 不存在，跳过"
    fi
}

# ============================================================
# 初始化数据库
# ============================================================
init_database() {
    print_header "初始化数据库"
    
    check_neo4j
    
    print_info "执行 Schema 初始化..."
    $PYTHON scripts/init_neo4j.py
    
    print_success "数据库初始化完成"
}

# ============================================================
# 导入示例数据
# ============================================================
import_sample_data() {
    print_header "导入示例数据"
    
    print_info "导入人物关系图谱示例数据..."
    $PYTHON scripts/import_people.py
    
    print_success "示例数据导入完成"
}

# ============================================================
# 启动服务
# ============================================================

# 启动 FastAPI
start_api() {
    print_info "启动 FastAPI 服务..."
    
    # 检查端口
    if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        print_warning "端口 8000 已被占用，跳过"
        return
    fi
    
    nohup $PYTHON -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload \
        > "$LOG_DIR/api.log" 2>&1 &
    echo $! > "$PID_DIR/api.pid"
    
    print_success "FastAPI 已启动 (PID: $(cat $PID_DIR/api.pid))"
    print_info "  地址: http://localhost:8000"
    print_info "  日志: $LOG_DIR/api.log"
}

# 启动 Streamlit 主界面
start_web() {
    print_info "启动 Streamlit 主界面..."
    
    # 检查端口
    if lsof -Pi :8501 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        print_warning "端口 8501 已被占用，跳过"
        return
    fi
    
    nohup $PYTHON -m streamlit run web/streamlit_app.py \
        --server.port 8501 \
        --server.headless true \
        > "$LOG_DIR/web.log" 2>&1 &
    echo $! > "$PID_DIR/web.pid"
    
    print_success "Streamlit 主界面已启动 (PID: $(cat $PID_DIR/web.pid))"
    print_info "  地址: http://localhost:8501"
    print_info "  日志: $LOG_DIR/web.log"
}

# 启动人物图谱界面
start_people_graph() {
    print_info "启动人物图谱界面..."
    
    # 检查端口
    if lsof -Pi :8502 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        print_warning "端口 8502 已被占用，跳过"
        return
    fi
    
    nohup $PYTHON -m streamlit run web/people_graph.py \
        --server.port 8502 \
        --server.headless true \
        > "$LOG_DIR/people_graph.log" 2>&1 &
    echo $! > "$PID_DIR/people_graph.pid"
    
    print_success "人物图谱界面已启动 (PID: $(cat $PID_DIR/people_graph.pid))"
    print_info "  地址: http://localhost:8502"
    print_info "  日志: $LOG_DIR/people_graph.log"
}

# 启动后台管理界面
start_admin() {
    print_info "启动后台管理界面..."
    
    # 检查端口
    if lsof -Pi :8503 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        print_warning "端口 8503 已被占用，跳过"
        return
    fi
    
    nohup $PYTHON -m streamlit run web/admin.py \
        --server.port 8503 \
        --server.headless true \
        > "$LOG_DIR/admin.log" 2>&1 &
    echo $! > "$PID_DIR/admin.pid"
    
    print_success "后台管理界面已启动 (PID: $(cat $PID_DIR/admin.pid))"
    print_info "  地址: http://localhost:8503"
    print_info "  日志: $LOG_DIR/admin.log"
}

# ============================================================
# 停止服务
# ============================================================
stop_all() {
    print_header "停止所有服务"
    
    # 停止 Python 服务
    for pid_file in "$PID_DIR"/*.pid; do
        if [ -f "$pid_file" ]; then
            pid=$(cat "$pid_file")
            name=$(basename "$pid_file" .pid)
            
            if kill -0 "$pid" 2>/dev/null; then
                kill "$pid" 2>/dev/null
                print_info "停止 $name (PID: $pid)"
            fi
            
            rm -f "$pid_file"
        fi
    done
    
    # 询问是否停止 Docker 容器
    echo ""
    read -p "是否停止 Docker 容器 (Neo4j/Redis)? (y/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if command -v docker &> /dev/null; then
            docker stop graphrag-neo4j graphrag-redis 2>/dev/null || true
            print_info "Docker 容器已停止"
        fi
    fi
    
    print_success "所有服务已停止"
}

# ============================================================
# 查看状态
# ============================================================
show_status() {
    print_header "服务状态"
    
    services=("api:8000:FastAPI" "web:8501:主界面" "people_graph:8502:人物图谱" "admin:8503:后台管理")
    
    for svc in "${services[@]}"; do
        IFS=':' read -r name port desc <<< "$svc"
        pid_file="$PID_DIR/$name.pid"
        
        if [ -f "$pid_file" ] && kill -0 "$(cat "$pid_file")" 2>/dev/null; then
            echo -e "  ${GREEN}●${NC} $desc - http://localhost:$port (PID: $(cat "$pid_file"))"
        else
            echo -e "  ${RED}○${NC} $desc - 未运行"
        fi
    done
    
    echo ""
}

# ============================================================
# 查看日志
# ============================================================
show_logs() {
    local service=${1:-"api"}
    local log_file="$LOG_DIR/$service.log"
    
    if [ -f "$log_file" ]; then
        tail -f "$log_file"
    else
        print_error "日志文件不存在: $log_file"
    fi
}

# ============================================================
# 打印使用说明
# ============================================================
print_usage() {
    print_header "启动完成"
    
    echo -e "${GREEN}🎉 所有服务已启动！${NC}"
    echo ""
    echo "访问地址:"
    echo "  - FastAPI 文档: http://localhost:8000/docs"
    echo "  - 主界面:       http://localhost:8501"
    echo "  - 人物图谱:     http://localhost:8502"
    echo "  - 后台管理:     http://localhost:8503"
    echo ""
    echo "常用命令:"
    echo "  ./dev.sh status   - 查看服务状态"
    echo "  ./dev.sh stop     - 停止所有服务"
    echo "  ./dev.sh logs     - 查看日志 (默认 api)"
    echo "  ./dev.sh logs web - 查看主界面日志"
    echo ""
}

# ============================================================
# 主函数
# ============================================================
main() {
    local command=${1:-"start"}
    
    case "$command" in
        start)
            print_header "Multimodal Graph RAG - 本地调试启动"
            
            check_python
            install_deps
            check_neo4j
            check_redis_optional
            init_database
            
            # 询问是否导入示例数据
            if [ ! -f "$PID_DIR/.imported" ]; then
                echo ""
                read -p "是否导入示例数据? (y/N): " -n 1 -r
                echo ""
                if [[ $REPLY =~ ^[Yy]$ ]]; then
                    import_sample_data
                    touch "$PID_DIR/.imported"
                fi
            fi
            
            # 启动所有服务
            start_api
            start_web
            start_people_graph
            start_admin
            
            print_usage
            ;;
            
        stop)
            stop_all
            ;;
            
        status)
            show_status
            ;;
            
        logs)
            show_logs "${2:-api}"
            ;;
            
        restart)
            stop_all
            sleep 2
            main start
            ;;
            
        init)
            print_header "初始化数据库"
            check_python
            check_neo4j
            init_database
            ;;
            
        import)
            print_header "导入示例数据"
            check_python
            check_neo4j
            import_sample_data
            ;;
            
        install)
            print_header "安装依赖"
            check_python
            install_deps
            ;;
            
        help|--help|-h)
            echo "用法: ./dev.sh [命令]"
            echo ""
            echo "命令:"
            echo "  start    - 启动所有服务 (默认)"
            echo "  stop     - 停止所有服务"
            echo "  restart  - 重启所有服务"
            echo "  status   - 查看服务状态"
            echo "  logs     - 查看日志 (默认 api)"
            echo "  init     - 初始化数据库"
            echo "  import   - 导入示例数据"
            echo "  install  - 安装依赖"
            echo "  help     - 显示帮助"
            ;;
            
        *)
            print_error "未知命令: $command"
            echo "使用 ./dev.sh help 查看帮助"
            exit 1
            ;;
    esac
}

main "$@"
