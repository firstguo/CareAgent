## 1. 项目初始化

- [x] 1.1 创建项目目录结构（services/、gateway/、frontend/、config/、keys/）
- [x] 1.2 创建.gitignore文件（排除.env、keys/、__pycache__、.venv等）
- [x] 1.3 创建.env.example模板文件（包含所有必需的环境变量）
- [x] 1.4 生成JWT密钥对（RSA 2048位私钥和公钥）
- [x] 1.5 创建docker-compose.yml基础框架

## 2. 基础设施服务

- [x] 2.1 配置Milvus Docker容器（etcd + minio + milvus）
- [x] 2.2 配置Redis Docker容器（端口6379）
- [x] 2.3 验证基础设施服务启动和健康检查

## 3. MCP Gateway部署

- [x] 3.1 克隆IBM ContextForge仓库或拉取Docker镜像
- [x] 3.2 配置Gateway路由规则（user.*、memory.*、speech.*、vision.*、llm.*、schedule.*）
- [x] 3.3 配置JWT认证（RS256公钥路径）
- [x] 3.4 配置Redis限流（用户30次/分钟，全局200次/分钟）
- [x] 3.5 配置Prometheus metrics端点（/metrics）
- [x] 3.6 启动Gateway并验证路由功能

## 4. User MCP Server

- [x] 4.1 创建user-service项目结构（FastAPI + MCP SDK）
- [x] 4.2 实现用户数据模型（使用Milvus存储）
- [x] 4.3 实现user.create_user工具（支持elder/child/caregiver角色）
- [x] 4.4 实现user.get_user工具（查询用户信息）
- [x] 4.5 实现user.update_user工具（更新用户信息）
- [x] 4.6 实现user.delete_user工具（软删除）
- [x] 4.7 实现user.switch_user工具（看护人切换用户）
- [x] 4.8 实现user.set_voice_preference和get_voice_preference工具
- [x] 4.9 添加单元测试
- [x] 4.10 配置Dockerfile和docker-compose服务

## 5. Memory MCP Server

- [x] 5.1 创建memory-service项目结构
- [x] 5.2 集成Mem0库并配置Milvus后端
- [x] 5.3 实现memory.add工具（添加事实、偏好、事件记忆）
- [x] 5.4 实现memory.search工具（语义检索，支持top_k参数）
- [x] 5.5 实现memory.update工具（更新记忆内容）
- [x] 5.6 实现memory.delete工具（删除记忆）
- [x] 5.7 实现memory.get_conversation_history工具（查询对话历史）
- [x] 5.8 实现memory.get_user_profile工具（生成用户画像摘要）
- [x] 5.9 添加单元测试
- [x] 5.10 配置Dockerfile和docker-compose服务

## 6. LLM MCP Server

- [x] 6.1 创建llm-service项目结构
- [x] 6.2 集成LangChain框架和通义千问ChatOpenAI接口
- [x] 6.3 实现llm.chat工具（单轮对话）
- [x] 6.4 实现llm.chat_stream工具（流式输出）
- [x] 6.5 配置LangChain PromptTemplate管理系统
- [x] 6.6 实现Prefix Cache机制（显式和隐式缓存）
- [x] 6.7 实现分级模型路由（Turbo/Plus/Max基于意图）
- [x] 6.8 实现llm.summarize工具（文本摘要）
- [x] 6.9 实现意图识别功能（medication_query/emergency等）
- [x] 6.10 添加单元测试
- [x] 6.11 配置Dockerfile和docker-compose服务

## 7. Speech MCP Server

- [x] 7.1 创建speech-service项目结构
- [x] 7.2 集成阿里云ASR SDK
- [x] 7.3 实现speech.transcribe工具（语音识别，16kHz WAV）
- [x] 7.4 集成阿里云TTS SDK
- [x] 7.5 实现speech.synthesize工具（文本转语音，支持音色选择）
- [x] 7.6 实现speech.list_voices工具（获取可用音色列表）
- [x] 7.7 添加单元测试
- [x] 7.8 配置Dockerfile和docker-compose服务

## 8. Vision MCP Server

- [x] 8.1 创建vision-service项目结构
- [x] 8.2 集成通义千问Qwen-VL模型（通过LangChain）
- [x] 8.3 实现vision.analyze_image工具（图像内容分析）
- [x] 8.4 实现vision.detect_danger工具（危险场景检测）
- [x] 8.5 实现vision.assess_environment工具（环境安全评估）
- [x] 8.6 添加单元测试
- [x] 8.7 配置Dockerfile和docker-compose服务

## 9. Schedule MCP Server

- [x] 9.1 创建schedule-service项目结构
- [x] 9.2 实现定时任务数据模型（使用Milvus存储）
- [x] 9.3 实现schedule.create_reminder工具（创建定时任务）
- [x] 9.4 实现schedule.list_tasks工具（查询任务列表）
- [x] 9.5 实现schedule.update_task工具（更新任务）
- [x] 9.6 实现schedule.delete_task工具（删除任务）
- [x] 9.7 实现schedule.enable_task和disable_task工具（启停控制）
- [x] 9.8 实现重复规则逻辑（daily/weekly/monthly/weekday）
- [x] 9.9 集成APScheduler或Celery实现定时触发
- [x] 9.10 添加单元测试
- [x] 9.11 配置Dockerfile和docker-compose服务

## 10. 安全防护实现

- [x] 10.1 实现JWT Token签发和验证中间件（RS256）
- [x] 10.2 实现RBAC权限控制（elder/child/caregiver权限矩阵）
- [x] 10.3 实现Prompt注入检测（15+正则表达式模式）
- [x] 10.4 实现Redis滑动窗口限流器
- [x] 10.5 实现敏感配置加密加载（.env文件）
- [x] 10.6 配置密钥文件权限（keys/目录600权限）
- [x] 10.7 添加安全日志记录（拒绝请求、异常事件）

## 11. 可观测性实现

- [x] 11.1 配置MLflow Tracking Server（Docker部署）
- [x] 11.2 在LLM服务中集成MLflow回调（记录model、tokens、cost）
- [x] 11.3 为每个MCP Server添加Prometheus metrics端点
- [x] 11.4 配置Prometheus采集规则（prometheus.yml）
- [x] 11.5 配置Grafana数据源（Prometheus）
- [x] 11.6 创建Grafana Dashboard（服务健康、QPS、延迟、Token消耗）
- [x] 11.7 实现结构化日志（request_id、user_id、duration）
- [x] 11.8 配置日志聚合和检索

## 12. Web前端开发

- [x] 12.1 创建Streamlit项目结构
- [x] 12.2 实现侧边栏用户列表和切换功能
- [x] 12.3 集成streamlit-webrtc实现语音录制
- [x] 12.4 实现图片上传组件（文件选择和拖拽）
- [x] 12.5 实现对话历史显示组件（区分用户和AI消息）
- [x] 12.6 实现语音播放功能（TTS回复播放）
- [x] 12.7 实现任务管理界面（创建、查看、编辑定时任务）
- [x] 12.8 集成MCP Client连接Gateway
- [x] 12.9 实现错误处理和用户提示
- [x] 12.10 优化UI/UX（响应式设计、加载状态）

## 13. 集成测试

- [x] 13.1 编写端到端测试用例（完整对话流程）
- [x] 13.2 测试语音识别和合成链路
- [x] 13.3 测试图像上传和分析链路
- [x] 13.4 测试定时任务创建和触发
- [x] 13.5 测试记忆存储和检索
- [x] 13.6 测试用户切换和权限控制
- [x] 13.7 测试Prefix Cache命中率
- [x] 13.8 压力测试（并发请求、限流验证）

## 14. 文档和部署

- [x] 14.1 编写README.md（项目介绍、快速开始）
- [x] 14.2 编写API文档（MCP工具说明）
- [x] 14.3 编写部署文档（Docker Compose一键启动）
- [x] 14.4 编写开发文档（架构说明、贡献指南）
- [x] 14.5 完善docker-compose.yml（所有服务编排）
- [x] 14.6 创建健康检查脚本
- [x] 14.7 配置日志轮转和备份策略
- [x] 14.8 最终验证所有服务启动和通信
