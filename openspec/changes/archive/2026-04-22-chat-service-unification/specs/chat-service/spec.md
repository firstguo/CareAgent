## ADDED Requirements

### Requirement: Chat Service必须提供统一的多模态交互REST API
Chat Service SHALL提供两个REST端点：POST /api_planning用于提交异步任务，GET /api_task_status/{task_id}用于查询任务状态。

#### Scenario: 提交多模态任务
- **WHEN** 客户端POST /api_planning，携带user_id、语音数据和图像数据
- **THEN** 系统立即返回task_id和pending状态

#### Scenario: 查询任务状态
- **WHEN** 客户端GET /api_task_status/{task_id}，任务已完成
- **THEN** 系统返回completed状态、文本回复和语音回复数据

#### Scenario: 查询不存在的任务
- **WHEN** 客户端GET /api_task_status/{不存在的task_id}
- **THEN** 系统返回404 Not Found错误

### Requirement: Chat Service必须整合语音、视觉、LLM、记忆四大能力模块
Chat Service SHALL包含四个内部模块：modules/speech.py（阿里云ASR/TTS）、modules/vision.py（Qwen-VL）、modules/llm.py（LangChain + Qwen）、modules/memory.py（Milvus + Mem0）。

#### Scenario: 模块进程内调用
- **WHEN** Temporal Workflow执行语音识别步骤
- **THEN** 直接调用modules/speech.py的transcribe函数，无需HTTP请求

#### Scenario: 共享连接池
- **WHEN** 多个Workflow并发执行
- **THEN** 共享Milvus连接池和LLM客户端实例

### Requirement: Chat Service必须支持定时任务意图识别
当用户在对话中表达定时任务意图时，LLM SHALL识别并返回schedule信息供前端保存。

#### Scenario: 识别用药提醒意图
- **WHEN** 用户说"每天早上8点提醒我吃药"
- **THEN** LLM返回should_save_schedule=true，包含cron表达式"0 8 * * *"和任务类型medication_reminder

#### Scenario: 识别非定时任务意图
- **WHEN** 用户说"今天天气怎么样"
- **THEN** LLM返回should_save_schedule=false

### Requirement: Chat Service必须删除独立的speech/vision/llm/memory服务部署
原services/speech-service、services/vision-service、services/llm-service、services/memory-service SHALL从部署配置中移除。

#### Scenario: 从docker-compose删除旧服务
- **WHEN** 查看docker-compose.yml
- **THEN** 不存在speech-service、vision-service、llm-service、memory-service服务定义

#### Scenario: 删除服务目录
- **WHEN** 查看services/目录
- **THEN** 不存在speech-service、vision-service、llm-service、memory-service子目录
