## Context

CareAgent当前采用微服务架构，包含8个独立服务（user-service、memory-service、speech-service、vision-service、llm-service、schedule-service、gateway、frontend）。其中speech/vision/llm/memory四个服务作为MCP Server独立部署，存在服务间调用延迟高、上下文共享困难、运维复杂等问题。schedule-service的定时任务功能可由前端直接实现。

本次变更将这四个服务合并为统一的chat-service，采用REST API + Temporal工作流编排架构，简化部署结构，提升性能和可维护性。同时删除schedule-service，定时任务完全由前端localStorage和JS定时器管理。

**约束条件：**
- 手机端Web访问，需保持页面打开才能触发定时任务
- 不做PWA，使用纯Web方案
- 保留user-service和schedule-service作为独立MCP服务
- 使用阿里云通义千问系列模型和语音服务
- 使用Milvus作为向量数据库

## Goals / Non-Goals

**Goals:**
- 构建统一的Chat Service，整合语音、视觉、LLM、记忆四大能力
- 实现基于Temporal的DAG任务编排，支持多步骤异步执行
- 提供简洁的REST API (/api_planning, /api_task_status)
- 实现前端定时任务管理（localStorage + JS定时器）
- 简化部署架构，减少服务数量从8个到5个
- 提升性能，减少服务间网络调用延迟

**Non-Goals:**
- 不实现PWA或原生App
- 不实现离线定时任务触发（需保持页面打开）
- 不保留speech/vision/llm/memory/schedule的独立部署
- 不修改user-service的架构
- 不实现复杂的推送通知系统（FCM/APNs）

## Decisions

### 1. Chat Service采用REST API而非MCP协议

**决策**: Chat Service对外提供纯REST API，不作为MCP Server

**理由:**
- 前端只需调用两个接口，无需复杂的MCP工具调用
- REST API更直观，易于调试和测试
- 减少依赖（不需要MCP SDK）
- 异步任务模式更适合REST风格（提交任务→查询状态）

**替代方案:**
- 保持MCP协议：前端需要实现MCP客户端，增加复杂度
- 混合模式（REST + MCP）：增加维护成本，无实际收益

### 2. 使用Temporal进行DAG任务编排

**决策**: 采用Temporal作为工作流引擎

**理由:**
- 持久化执行：服务重启后工作流继续（vs asyncio.create_task会丢失）
- 自动重试：内置重试策略，LLM超时自动重试
- 可视化：Temporal UI可以查看工作流执行状态
- DAG支持：通过`gather`实现并行，通过`await`实现依赖
- 时间旅行调试：可以重放工作流历史

**替代方案:**
- asyncio.create_task()：轻量但无持久化，服务重启丢失任务
- Celery：需要Redis Broker，学习成本高，可视化弱
- Prefect/Dagster：重框架，不适合当前规模

### 3. MongoDB存储任务状态

**决策**: 使用MongoDB存储任务执行状态和结果

**理由:**
- 文档型数据库，适合存储动态结构的任务数据
- TTL索引支持自动清理过期数据（30天）
- 灵活的schema，任务步骤可动态扩展
- 与Temporal PostgreSQL元数据分离，职责清晰

**替代方案:**
- Milvus：向量数据库，不适合存储任务状态
- Redis：内存数据库，持久化不如MongoDB可靠
- PostgreSQL：关系型，schema变更不如MongoDB灵活

### 4. 前端localStorage存储定时任务

**决策**: 定时任务配置存储在前端localStorage，由JS定时器触发

**理由:**
- 极简实现，不需要后端定时触发逻辑
- 快速验证LLM意图识别核心功能
- 适合Demo/MVP阶段
- 手机端浏览器localStorage持久性好

**局限性与缓解:**
- [iOS后台JS暂停] → 提示用户保持页面打开
- [单设备限制] → Demo阶段可接受，后续可升级后端同步
- [离线无法触发] → 当前不做PWA，暂不考虑

**替代方案:**
- 后端Schedule Service触发：需要额外服务，增加复杂度
- PWA Service Worker：用户明确不做PWA

### 5. 服务合并策略

**决策**: 将speech/vision/llm/memory四个服务的代码迁移为chat-service的内部模块

**迁移映射:**
```
services/speech-service/main.py  → services/chat-service/modules/speech.py
services/vision-service/main.py  → services/chat-service/modules/vision.py
services/llm-service/main.py     → services/chat-service/modules/llm.py
services/memory-service/main.py  → services/chat-service/modules/memory.py
services/schedule-service/       → 删除（功能由前端实现）
```

**理由:**
- 代码复用，保留已实现的阿里云ASR/TTS、Qwen-VL、LangChain集成
- 进程内调用替代HTTP调用，降低延迟
- 共享连接池（Milvus、LLM客户端）

### 6. Temporal工作流设计

**CareTaskWorkflow结构:**
```
Step 1: speech.transcribe (条件：有音频输入)
Step 2: vision.analyze (条件：有图像输入)
Step 3: memory.retrieve (与Step 1,2并行)
Step 4: llm.plan (依赖Step 1,2,3)
Step 5: llm.chat (依赖Step 4)
Step 6: speech.synthesize (依赖Step 5)
Step 7: memory.store (依赖Step 5,6)
```

**理由:**
- 支持条件执行（语音/图像输入可选）
- 并行步骤减少总执行时间
- 清晰的依赖关系便于调试

### 7. Gateway路由精简

**决策**: Gateway仅保留user.*路由

**理由:**
- speech/vision/llm/memory已合并到chat-service
- schedule功能已迁移到前端localStorage
- 前端通过REST直接调用chat-service，不走Gateway
- 简化路由配置，降低Gateway负担

## Risks / Trade-offs

### [风险] 手机端浏览器后台暂停导致定时任务不触发
**影响**: iOS Safari切换到后台后JS定时器暂停，Android Chrome可能被杀后台
**缓解**: 
- 首次访问时提示用户"请保持页面打开"
- 使用visibilitychange API，回到前台时立即检查
- 建议用户添加到手机主屏幕（改善体验但非PWA）

### [风险] Chat Service单体过大，依赖复杂
**影响**: 包含ASR/TTS SDK、Qwen-VL、LangChain、Milvus等，依赖管理复杂
**缓解**:
- 使用requirements.txt明确版本
- Docker分层构建优化镜像大小
- 后续可按需拆分（如vision-service独立扩展）

### [风险] Temporal引入额外运维复杂度
**影响**: 需要维护Temporal Server、PostgreSQL元数据库、Temporal UI
**缓解**:
- Docker Compose一键部署
- Temporal auto-setup镜像自动初始化数据库
- Demo阶段可使用轻量模式

### [权衡] 定时任务数据仅存储在前端
**影响**: 无法跨设备同步，关闭浏览器后任务丢失
**缓解**: 
- Demo阶段可接受
- 预留升级路径：未来可同步到后端MongoDB
- LLM可在每次对话时重新创建任务

### [权衡] 异步任务需要轮询查询状态
**影响**: 前端需定时轮询/api_task_status，增加请求数
**缓解**:
- 轮询间隔可配置（建议2-5秒）
- 任务完成后停止轮询
- 未来可升级为WebSocket推送

## Migration Plan

### 阶段1: 基础设施准备
1. 在docker-compose.yml添加Temporal Server、MongoDB服务
2. 验证Temporal连接和MongoDB连接
3. 创建Temporal Worker配置

### 阶段2: Chat Service开发
1. 创建chat-service目录结构和FastAPI应用
2. 迁移speech/vision/llm/memory模块代码
3. 实现Temporal Workflow和Activities
4. 实现/api_planning和/api_task_status接口
5. 实现MongoDB任务状态管理

### 阶段3: 前端集成
1. 修改前端调用方式（REST API替代MCP工具调用）
2. 实现localStorage定时任务管理
3. 实现JS定时器和触发逻辑
4. 实现任务状态轮询和语音播放

### 阶段4: 清理旧服务
1. 更新Gateway路由配置（删除speech/vision/llm/memory/schedule路由）
2. 从docker-compose.yml删除5个旧服务
3. 删除services/speech-service等目录
4. 测试完整流程

### 回滚策略
- 保留旧服务代码在Git历史中
- 如出现问题，可恢复旧docker-compose.yml配置
- MongoDB数据不影响旧架构（旧架构不使用）

## Open Questions

1. **Temporal重试策略**: LLM调用的超时时间和重试次数需要根据实际API响应时间调整（待定）
2. **前端轮询间隔**: 需要平衡实时性和请求数，建议2-5秒（待测试）
3. **任务并发限制**: 同时执行的任务数量需要限制，避免资源耗尽（待压测）
4. **Milvus连接池**: 多个Activity共享Milvus连接的池化策略（待优化）
