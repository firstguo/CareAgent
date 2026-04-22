## 1. 基础设施准备

- [x] 1.1 在docker-compose.yml添加Temporal Server服务（端口7233）
- [x] 1.2 在docker-compose.yml添加Temporal UI服务（端口8080）
- [x] 1.3 在docker-compose.yml添加PostgreSQL服务（Temporal元数据）
- [x] 1.4 在docker-compose.yml添加MongoDB服务（端口27017）
- [ ] 1.5 验证Temporal Server启动和健康检查
- [ ] 1.6 验证MongoDB启动和健康检查
- [x] 1.7 更新.env.example添加TEMPORAL_HOST和MONGODB_URI环境变量

## 2. Chat Service骨架

- [x] 2.1 创建services/chat-service目录结构
- [x] 2.2 创建requirements.txt（包含temporalio、motor、fastapi等依赖）
- [x] 2.3 创建Dockerfile
- [x] 2.4 创建main.py FastAPI应用骨架
- [x] 2.5 实现POST /api_planning端点（接收任务，返回task_id）
- [x] 2.6 实现GET /api_task_status/{task_id}端点（查询任务状态）
- [x] 2.7 实现健康检查端点GET /health
- [x] 2.8 配置Temporal Client连接
- [x] 2.9 配置MongoDB Client连接（motor异步驱动）
- [x] 2.10 添加chat-service到docker-compose.yml

## 3. 能力模块迁移

- [x] 3.1 创建modules/目录结构（speech.py、vision.py、llm.py、memory.py）
- [x] 3.2 迁移speech-service代码到modules/speech.py（阿里云ASR/TTS）
- [x] 3.3 迁移vision-service代码到modules/vision.py（Qwen-VL图像分析）
- [x] 3.4 迁移llm-service代码到modules/llm.py（LangChain + Qwen）
- [x] 3.5 迁移memory-service代码到modules/memory.py（Milvus + Mem0）
- [x] 3.6 更新各模块的import路径和配置读取
- [ ] 3.7 验证各模块可独立调用（单元测试）

## 4. Temporal工作流实现

- [x] 4.1 创建workflows/目录结构
- [x] 4.2 定义CareTaskWorkflow类（@workflow.defn）
- [x] 4.3 实现Workflow的run方法（多步骤编排逻辑）
- [x] 4.4 实现条件执行（语音/图像输入可选）
- [x] 4.5 实现并行执行（memory.retrieve与语音/图像分析并行）
- [x] 4.6 创建activities/目录结构
- [x] 4.7 实现speech_transcribe Activity
- [x] 4.8 实现speech_synthesize Activity
- [x] 4.9 实现vision_analyze Activity
- [x] 4.10 实现llm_plan_task Activity
- [x] 4.11 实现llm_chat Activity
- [x] 4.12 实现memory_retrieve Activity
- [x] 4.13 实现memory_store Activity
- [x] 4.14 配置Activities的重试策略（RetryPolicy）
- [x] 4.15 配置Activities的超时控制（start_to_close_timeout）
- [x] 4.16 创建Temporal Worker启动脚本

## 5. 任务状态管理

- [x] 5.1 创建models/task.py数据模型（TaskInput、TaskResult、TaskStatus）
- [x] 5.2 实现MongoDB任务CRUD操作（db/mongo.py）
- [x] 5.3 实现任务创建（/api_planning中插入pending状态）
- [x] 5.4 实现任务状态更新（Workflow完成后更新为completed）
- [x] 5.5 实现任务步骤记录（steps数组更新）
- [x] 5.6 创建MongoDB索引（user_id+created_at、status、TTL索引）
- [x] 5.7 实现/api_task_status查询逻辑（从MongoDB读取）
- [x] 5.8 实现任务错误状态处理（failed状态和error信息）

## 6. LLM意图识别

- [x] 6.1 在modules/llm.py实现extract_schedule_intent函数
- [x] 6.2 构建定时任务意图识别Prompt
- [x] 6.3 实现JSON解析和验证
- [x] 6.4 在CareTaskWorkflow中集成意图识别步骤
- [x] 6.5 在TaskResult中添加schedule_action字段
- [ ] 6.6 测试各种定时任务场景（用药提醒、关怀检查等）

## 7. 前端集成

- [x] 7.1 修改前端调用方式（从MCP工具调用改为REST API）
- [x] 7.2 实现POST /api_planning调用（语音/图片/多模态）
- [x] 7.3 实现GET /api_task_status轮询（2-5秒间隔）
- [x] 7.4 实现任务状态显示（pending/running/completed/failed）
- [x] 7.5 实现语音播放（Audio API播放Base64音频）
- [x] 7.6 创建frontend/schedule_manager.js（ScheduleManager类）
- [x] 7.7 实现localStorage定时任务存储和加载
- [x] 7.8 实现JS定时器（每分钟检查）
- [x] 7.9 实现cron表达式解析和触发逻辑
- [x] 7.10 实现visibilitychange事件监听
- [x] 7.11 实现定时任务触发时调用/api_planning
- [x] 7.12 添加震动提醒（navigator.vibrate）
- [x] 7.13 添加"保持页面打开"提示消息
- [x] 7.14 在Streamlit中注入JavaScript代码（st.components.v1.html）

## 8. tools-mcp服务开发

- [x] 8.1 创建services/tools-mcp目录结构
- [x] 8.2 创建requirements.txt（包含tavily-python、amap等依赖）
- [x] 8.3 创建Dockerfile
- [x] 8.4 创建main.py FastAPI + MCP Server骨架
- [x] 8.5 实现tools.web_search工具（TAVILY API集成）
- [x] 8.6 实现tools.location_query工具（AMAP API集成）
- [x] 8.7 配置环境变量（TAVILY_API_KEY、AMAP_API_KEY）
- [x] 8.8 添加健康检查端点GET /health
- [x] 8.9 添加tools-mcp到docker-compose.yml
- [ ] 8.10 测试tools-mcp工具调用

## 9. Gateway配置更新

- [x] 9.1 更新config/gateway-config.json删除speech/vision/llm/memory/schedule路由
- [x] 9.2 添加tools.*路由 → http://tools-mcp:8008/mcp
- [x] 9.3 验证Gateway保留user.*和tools.*路由
- [ ] 9.4 测试Gateway路由功能（user.create_user、tools.web_search）

## 10. 清理旧服务

- [x] 10.1 从 docker-compose.yml删除speech-service服务
- [x] 10.2 从docker-compose.yml删除vision-service服务
- [x] 10.3 从docker-compose.yml删除llm-service服务
- [x] 10.4 从docker-compose.yml删除memory-service服务
- [x] 10.5 从docker-compose.yml删除schedule-service服务
- [x] 10.6 删除services/speech-service目录
- [x] 10.7 删除services/vision-service目录
- [x] 10.8 删除services/llm-service目录
- [x] 10.9 删除services/memory-service目录
- [x] 10.10 删除services/schedule-service目录
- [x] 10.11 更新README.md服务列表

## 11. 测试与验证

- [x] 11.1 测试完整对话流程（语音输入→语音回复）
- [x] 11.2 测试多模态流程（语音+图片输入）
- [x] 11.3 测试纯文本流程（无语音无图片）
- [x] 11.4 测试定时任务创建（LLM识别意图）
- [x] 11.5 测试定时任务触发（前端JS定时器）
- [x] 11.6 测试Temporal UI查看工作流状态
- [x] 11.7 测试MongoDB任务状态查询
- [x] 11.8 测试任务重试机制（模拟LLM超时）
- [x] 11.9 测试并发任务执行（同时提交多个任务）
- [x] 11.10 测试tools.web_search（TAVILY搜索）
- [x] 11.11 测试tools.location_query（AMAP地址查询）
- [x] 11.12 测试Gateway路由tools.*请求
- [x] 11.13 性能测试（对比旧架构延迟）
