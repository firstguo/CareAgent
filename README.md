# CareAgent
智能看护助手 - 基于AI的多模态交互系统

## 📋 项目简介

CareAgent 是一个智能看护助手，通过多模态交互（语音、文本、图像）帮助用户照顾老年人和小朋友。系统支持任务编排、定时提醒、记忆管理等功能。

## 🏗️ 架构概览

### 服务列表

| 服务 | 端口 | 描述 |
|------|------|------|
| **chat-service** | 8007 | 统一的多模态交互服务（语音+视觉+LLM+记忆） |
| **user-service** | 8001 | 用户管理MCP服务 |
| **tools-mcp** | 8008 | 工具服务（Web搜索+地址查询） |
| **gateway** | 4444 | MCP网关 |
| **frontend** | 8501 | Streamlit Web前端 |

### 基础设施

| 组件 | 端口 | 描述 |
|------|------|------|
| **Temporal Server** | 7233 | 工作流引擎（DAG任务编排） |
| **Temporal UI** | 8080 | 工作流监控界面 |
| **MongoDB** | 27017 | 任务状态存储 |
| **Milvus** | 19530 | 向量数据库（记忆存储） |
| **Redis** | 6379 | 缓存和限流 |

## 🚀 快速开始

### 1. 环境准备

```bash
# 复制环境变量配置
cp .env.example .env

# 编辑.env文件，填入API密钥
# - DASHSCOPE_API_KEY (通义千问)
# - ALIYUN_ACCESS_KEY_ID/SECRET (阿里云语音)
# - TAVILY_API_KEY (Web搜索)
# - AMAP_API_KEY (高德地图)
```

### 2. 启动服务

```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f chat-service
```

### 3. 访问服务

- **前端界面**: http://localhost:8501
- **Temporal UI**: http://localhost:8080
- **Gateway**: http://localhost:4444

## 📡 API文档

### Chat Service REST API

#### POST /api_planning
提交任务，异步执行

```bash
curl -X POST http://localhost:8007/api_planning \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_001",
    "trigger_type": "user_initiated",
    "input": {
      "type": "text",
      "text": "你好"
    }
  }'
```

响应:
```json
{
  "task_id": "task_abc123",
  "status": "pending",
  "message": "任务已提交，正在处理中"
}
```

#### GET /api_task_status/{task_id}
查询任务状态

```bash
curl http://localhost:8007/api_task_status/task_abc123
```

响应:
```json
{
  "task_id": "task_abc123",
  "status": "completed",
  "result": {
    "final_response": "你好！有什么可以帮助你的？",
    "audio_response": "base64音频数据..."
  }
}
```

## 🔧 核心功能

### 1. 多模态对话
- 语音识别（阿里云ASR）
- 语音合成（阿里云TTS）
- 图像分析（Qwen-VL）
- 文本对话（通义千问）

### 2. 任务编排
使用Temporal实现DAG工作流：
```
用户输入 → [语音识别/视觉分析] → 记忆检索 → LLM规划 → 执行步骤 → 返回结果
```

### 3. 定时任务
前端JavaScript实现：
- localStorage存储定时任务
- Cron表达式解析
- 自动触发调用Chat Service
- 震动提醒和浏览器通知

### 4. 记忆管理
- 向量存储（Milvus）
- 语义搜索
- 用户画像

### 5. 工具服务
- Web搜索（TAVILY）
- 地址查询（AMAP）
- 天气查询

## 📁 项目结构

```
CareAgent/
├── services/
│   ├── chat-service/          # 核心服务（语音+视觉+LLM+记忆）
│   │   ├── main.py            # FastAPI应用
│   │   ├── worker.py          # Temporal Worker
│   │   ├── modules/           # 能力模块
│   │   │   ├── speech.py      # 语音服务
│   │   │   ├── vision.py      # 视觉服务
│   │   │   ├── llm.py         # LLM服务
│   │   │   └── memory.py      # 记忆服务
│   │   ├── workflows/         # Temporal工作流
│   │   └── activities/        # Temporal活动
│   ├── user-service/          # 用户管理
│   └── tools-mcp/             # 工具服务
├── frontend/                  # Streamlit前端
│   ├── app.py
│   └── js/
│       ├── schedule_manager.js
│       └── chat_service_client.js
├── gateway/                   # MCP网关
├── config/                    # 配置文件
├── docker-compose.yml         # 服务编排
└── .env.example               # 环境变量示例
```

## 🛠️ 技术栈

- **后端**: FastAPI, Python 3.11
- **工作流**: Temporal
- **LLM**: LangChain + 通义千问
- **语音**: 阿里云NLS
- **视觉**: Qwen-VL
- **向量数据库**: Milvus + Mem0
- **任务存储**: MongoDB
- **缓存**: Redis
- **前端**: Streamlit + JavaScript

## 📝 开发指南

### 添加新的Activity

1. 在 `services/chat-service/activities/task_activities.py` 中定义函数
2. 使用 `@activity.defn(name="...")` 装饰器
3. 在 `worker.py` 中注册到Worker

### 修改工作流

编辑 `services/chat-service/workflows/care_task_workflow.py`，修改DAG编排逻辑。

### 前端开发

前端JavaScript代码位于 `frontend/js/`，通过Streamlit的 `st.components.v1.html` 注入。

## 🔍 监控

- **Temporal UI**: http://localhost:8080 - 查看工作流状态
- **Prometheus**: 指标监控
- **健康检查**: 各服务的 `/health` 端点

## ⚠️ 注意事项

1. **定时任务**: 需要保持浏览器页面打开，关闭页面将导致定时任务失效
2. **API密钥**: 必须在 `.env` 中配置所有必需的API密钥
3. **资源需求**: 完整启动所有服务约需4GB内存

## 📄 License

MIT
