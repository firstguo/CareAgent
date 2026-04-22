#!/bin/bash

# ============================================
# CareAgent 健康检查脚本
# 验证所有基础设施服务是否正常启动
# ============================================

echo "======================================"
echo "CareAgent 基础设施健康检查"
echo "======================================"
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查服务状态
check_service() {
    local service_name=$1
    local health_url=$2
    
    echo -n "检查 $service_name ... "
    
    if curl -s -f "$health_url" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ 正常${NC}"
        return 0
    else
        echo -e "${RED}✗ 异常${NC}"
        return 1
    fi
}

# 等待服务启动
wait_for_service() {
    local service_name=$1
    local health_url=$2
    local max_attempts=${3:-30}
    local wait_time=${4:-2}
    
    echo -n "等待 $service_name 启动 ..."
    
    for i in $(seq 1 $max_attempts); do
        if curl -s -f "$health_url" > /dev/null 2>&1; then
            echo -e " ${GREEN}✓ 已就绪${NC}"
            return 0
        fi
        sleep $wait_time
    done
    
    echo -e " ${RED}✗ 超时${NC}"
    return 1
}

# 检查Docker Compose服务
echo "1. 检查Docker Compose服务状态"
echo "--------------------------------------"
docker-compose ps
echo ""

# 等待并检查基础设施服务
echo "2. 等待基础设施服务就绪"
echo "--------------------------------------"

wait_for_service "Redis" "http://localhost:6379" 30 2
wait_for_service "Milvus" "http://localhost:9091/healthz" 60 5
wait_for_service "Etcd" "http://localhost:2379/health" 30 2
wait_for_service "MinIO" "http://localhost:9000/minio/health/live" 30 2

echo ""
echo "3. 检查监控服务"
echo "--------------------------------------"

wait_for_service "MLflow" "http://localhost:5000/health" 30 2
wait_for_service "Prometheus" "http://localhost:9090/-/healthy" 30 2
wait_for_service "Grafana" "http://localhost:3000/api/health" 30 2

echo ""
echo "======================================"
echo "健康检查完成！"
echo "======================================"
echo ""
echo "服务访问地址："
echo "  - Milvus:        http://localhost:19530"
echo "  - Redis:         localhost:6379"
echo "  - MLflow:        http://localhost:5000"
echo "  - Prometheus:    http://localhost:9090"
echo "  - Grafana:       http://localhost:3000"
echo ""
