## Why

CareAgent需要构建一个面向看护场景的AI Agent系统，服务于老年人、小朋友和看护人三类角色。当前项目处于初始状态，需要从零开始构建完整的MCP（Model Context Protocol）架构，实现多模态交互、智能看护、长期记忆等核心能力，并建立生产级的可观测性和安全防护体系。

## What Changes

- 构建基于IBM ContextForge的MCP Gateway架构，实现统一的服务路由和鉴权
- 开发6个独立部署的MCP Server（User、Memory、Speech、Vision、LLM、Schedule）
- 实现多用户多角色系统（老年人、小朋友、看护人）及其权限控制
- 使用LangChain框架构建LLM应用，集成通义千问系列模型（Qwen-Max/Plus/Turbo）和Qwen-VL视觉模型
- 集成阿里云语音服务（ASR语音识别、TTS语音合成）
- 实现基于Mem0 + Milvus的向量记忆系统，支持长期记忆和语义检索
- 开发Streamlit单页面Web应用，支持语音录制、图片上传和实时对话
- 实现Prefix Cache优化，降低Token成本60%以上
- 构建MLflow + Prometheus + Grafana可观测性体系
- 实施JWT认证、RBAC权限控制、正则表达式安全防护和频率控制
- 实现定时任务系统（用药提醒、主动关怀等）

## Capabilities

### New Capabilities

- `mcp-gateway`: MCP Gateway服务，负责路由分发、JWT认证、速率限制和监控
- `user-management`: 用户管理服务，支持多角色用户的CRUD和权限控制
- `memory-system`: 基于Mem0 + Milvus的向量记忆系统，支持长期记忆存储和语义检索
- `speech-service`: 语音服务，集成阿里云ASR和TTS，支持多音色选择
- `vision-service`: 视觉服务，集成Qwen-VL进行图像分析和风险识别
- `llm-service`: 大语言模型服务，集成通义千问，支持Prefix Cache和分级模型路由
- `schedule-service`: 定时任务服务，支持用药提醒、主动关怀等定时触发
- `web-frontend`: Streamlit Web界面，支持多模态输入和实时对话
- `observability`: 可观测性体系，包括MLflow实验追踪、Prometheus指标和Grafana面板
- `security`: 安全防护体系，包括JWT认证、RBAC、正则过滤和频率控制

### Modified Capabilities

<!-- 无现有能力需要修改 -->

## Impact

- **新增服务**: 6个独立MCP Server + 1个MCP Gateway
- **外部依赖**: 阿里云DashScope API、阿里云语音服务、LangChain、Mem0、Milvus、MLflow、Prometheus、Grafana
- **基础设施**: Docker Compose编排、Redis缓存、Milvus向量数据库
- **安全**: JWT密钥管理、API Key管理、加密配置
- **监控**: MLflow Tracking Server、Prometheus采集、Grafana Dashboard
- **前端**: Streamlit单页面应用，集成streamlit-webrtc语音录制
