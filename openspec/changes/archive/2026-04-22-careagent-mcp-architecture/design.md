## Context

CareAgent是一个全新的看护类AI Agent系统，当前项目处于初始状态（仅有README）。需要从零构建完整的MCP架构系统，包括：
- 6个独立部署的MCP Server
- 1个IBM ContextForge MCP Gateway
- Streamlit Web前端
- 完整的可观测性和安全防护体系

**约束条件：**
- 使用阿里云通义千问系列模型
- 支持三类角色：老年人、小朋友、看护人
- 需要语音交互和图像识别能力
- Demo阶段，但需要生产级架构
- 必须实现Token成本优化（Prefix Cache）

## Goals / Non-Goals

**Goals:**
- 构建可扩展的MCP架构，支持未来增加更多服务
- 实现多模态交互（语音、图像、文字）
- 建立长期记忆系统，支持个性化看护
- 实现60%以上的Token成本节约
- 构建完整的可观测性体系（MLflow + Prometheus + Grafana）
- 实施OWASP Agentic安全框架
- 支持定时任务和主动关怀

**Non-Goals:**
- 移动端应用（后续迭代）
- 多Agent协作（后续迭代）
- 实时视频流处理
- 医疗诊断功能（仅提供信息和建议）
- 离线部署能力

## Decisions

### 1. MCP Gateway选择

**决策**: 使用IBM ContextForge开源实现

**理由:**
- 企业级功能：认证、路由、限流、监控
- 支持多种协议（MCP、REST、gRPC）
- 内置Admin UI和OpenTelemetry
- 活跃的开源社区
- 可通过Docker快速部署

**替代方案:**
- 自研简单Gateway：开发成本高，功能不完整
- 无Gateway直连：缺乏统一管理，不适合生产

### 2. MCP Server部署方式

**决策**: 独立Docker容器部署

**理由:**
- 进程隔离，故障不影响其他服务
- 独立扩展能力强服务（如LLM）
- 便于监控和调试
- 符合微服务最佳实践

**替代方案:**
- 进程内部署：简单但不利于扩展
- Kubernetes：过度复杂，不适合Demo

### 3. 大模型策略

**决策**: 分级模型路由（Turbo/Plus/Max）

**理由:**
- 简单问题用Turbo（低成本）
- 复杂分析用Max（高质量）
- 平衡性能和成本
- 配合Prefix Cache节约60%+ Token

**替代方案:**
- 单一模型：无法优化成本
- 全部用Max：成本过高

### 4. 大模型框架

**决策**: LangChain

**理由:**
- 成熟的LLM应用开发框架，提供统一的API抽象
- 内置通义千问集成（ChatOpenAI兼容接口）
- 提供Chain、Agent、Memory等核心组件
- 支持Prompt模板管理和链式调用
- 丰富的生态系统和工具集成
- 便于实现流式输出、回调机制
- 社区活跃，文档完善

**替代方案:**
- LlamaIndex：更适合RAG场景，但Agent能力较弱
- 原生SDK：灵活但需要自行封装通用逻辑
- Haystack：功能全面但学习曲线陡峭

### 5. 记忆系统

**决策**: Mem0 + Milvus

**理由:**
- Mem0提供开箱即用的记忆管理和智能检索
- Milvus是专业的向量数据库，性能卓越
- 支持海量向量数据的快速相似度搜索
- 支持多种索引类型（IVF_FLAT, HNSW, IVF_PQ等）
- 分布式架构，易于水平扩展
- 成熟的生态系统和完善的技术支持
- Mem0官方推荐的后端存储之一

**替代方案:**
- ChromaDB：轻量级但性能和扩展性有限
- Qdrant：功能类似但Milvus生态更成熟

### 6. 语音方案

**决策**: streamlit-webrtc + 阿里云ASR/TTS

**理由:**
- streamlit-webrtc支持实时录音
- 阿里云语音服务稳定可靠
- 支持多音色选择
- 与Streamlit集成简单

**替代方案:**
- 文件上传：用户体验差
- OpenAI Whisper：需要额外API

### 7. 可观测性

**决策**: MLflow + Prometheus + Grafana

**理由:**
- MLflow：AI实验追踪和模型管理
- Prometheus：实时指标采集
- Grafana：统一可视化
- 互补优势，各司其职

**替代方案:**
- 仅Prometheus：缺乏AI实验管理
- 仅MLflow：缺乏实时监控

### 8. 安全防护

**决策**: JWT + RBAC + 正则过滤 + 限流

**理由:**
- JWT RS256非对称加密，安全可靠
- RBAC实现细粒度权限控制
- 正则表达式过滤Prompt注入
- Redis滑动窗口限流防滥用
- 符合OWASP Agentic安全框架

### 9. Token优化

**决策**: 强制启用Prefix Cache + 6层优化

**理由:**
- 阿里云支持显式和隐式缓存
- System Prompt + 用户档案可缓存
- 配合Prompt优化、记忆分级、对话摘要
- 预期节约65-70%成本

## Risks / Trade-offs

### 风险1: 复杂度高
**风险**: 7个独立服务（6 MCP + Gateway）增加运维复杂度
**缓解**: 
- Docker Compose一键启动
- 完善的日志和监控
- 健康检查自动重启

### 风险2: 阿里云API成本
**风险**: 频繁调用可能产生高额费用
**缓解**:
- Prefix Cache优化（节约60%+）
- 分级模型路由
- 缓存常见问答
- 设置预算告警

### 风险3: streamlit-webrtc兼容性
**风险**: 某些浏览器可能不支持WebRTC
**缓解**:
- 提供文本输入降级方案
- 使用Google公共STUN服务器
- 测试主流浏览器

### 风险4: Milvus运维复杂度
**风险**: Milvus增加运维复杂度
**缓解**:
- Milvus使用Docker Compose简化部署
- Milvus配置合理的索引类型和资源限制
- 限制检索结果数量（Top-K）
- 缓存高频查询结果到Redis
- 监控Milvus服务状态和性能指标

### 风险5: 安全防护误杀
**风险**: 正则表达式可能误判正常输入
**缓解**:
- 分级处理（高危拒绝，中低危警告）
- 持续优化正则模式
- 提供申诉机制

### Trade-off: Demo vs 生产
**决策**: 采用生产级架构，但简化配置
**影响**:
- 开发时间增加30%
- 但代码可直接用于生产
- 避免后续重构

## Migration Plan

### 部署步骤

1. **准备阶段**
   ```bash
   # 克隆项目
   git clone <repo>
   cd CareAgent
   
   # 配置环境变量
   cp .env.example .env
   # 编辑填入API Key、JWT密钥等
   
   # 生成JWT密钥对
   openssl genrsa -out keys/private.pem 2048
   openssl rsa -in keys/private.pem -pubout -out keys/public.pem
   ```

2. **启动服务**
   ```bash
   # 一键启动所有服务
   docker-compose up -d
   
   # 验证服务
   docker-compose ps
   ```

3. **验证功能**
   - 访问Streamlit: http://localhost:8501
   - 访问MLflow: http://localhost:5000
   - 访问Grafana: http://localhost:3000
   - 测试语音、图像、对话功能

### 回滚策略
- 保留Docker镜像版本
- 数据库定期备份
- 配置文件版本控制

## Open Questions

1. **阿里云内容安全API**: 是否启用？（增加成本但提升安全性）
   - 建议：Demo阶段先不启用，后续根据需求添加

2. **Token预算**: Demo阶段的月度预算设定？
   - 建议：¥200-500/月（足够测试）

3. **多语言支持**: 是否需要支持英文等其他语言？
   - 建议：Demo阶段仅中文，后续扩展

4. **数据保留策略**: 对话历史保留多长时间？
   - 建议：90天完整数据，之后摘要归档
