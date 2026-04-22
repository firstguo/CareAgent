FROM node:18-alpine

# 安装IBM ContextForge MCP Gateway
RUN npm install -g @ibm/contextforge-gateway

WORKDIR /app

# 复制配置文件
COPY config/gateway-config.json /app/config.json

# 暴露端口
EXPOSE 4444

# 启动Gateway
CMD ["contextforge-gateway", "--config", "/app/config.json"]
