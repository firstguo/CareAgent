## Context

当前CareAgent的摔倒检测基于静态图片分析（`vision.py`的`detect_danger`函数），通过Qwen-VL单帧图像判断风险等级。这种方式存在明显的误报问题：无法区分"老人主动躺下休息"和"意外摔倒"，因为两者在单帧图像中可能呈现相似的姿态。

项目已有基础设施：
- Temporal Workflow编排能力
- Qwen-VL视觉模型集成
- MongoDB任务存储
- Streamlit前端测试页面
- FastAPI REST API

## Goals / Non-Goals

**Goals:**
- 通过视频时序分析降低摔倒检测误报率80%以上
- 实现前端上传视频文件、后端异步分析的完整流程
- 保留现有图片检测能力（向后兼容）
- 提供可测试的Phase 1方案（文件上传而非实时录制）

**Non-Goals:**
- 不支持实时视频流分析（Phase 2考虑）
- 不实现传感器自动触发（Phase 2考虑）
- 不做移动端App录制（Phase 2考虑）
- 不替代现有图片检测功能

## Decisions

### 1. 视频处理方式：后端抽帧分析

**决策**: 前端上传完整视频文件，后端使用OpenCV解码并均匀抽取5帧，逐帧调用现有Qwen-VL分析。

** alternatives considered:**
- ❌ 前端抽帧：前端兼容性问题多，且丢失视频格式控制能力
- ❌ 专用视频模型（Qwen2-VL）：需要额外API配置，成本高，Phase 1先验证价值
- ✅ 后端抽帧+现有模型：复用现有代码，实施成本低，可快速验证

**Rationale**: Phase 1目标是验证"视频时序分析能否降低误报率"，而非追求最优技术方案。复用Qwen-VL可以快速验证业务价值。

### 2. 抽帧策略：均匀抽帧

**决策**: 8秒视频均匀抽取5帧（约每1.6秒1帧）。

**Alternatives considered:**
- ❌ 关键帧抽帧：依赖视频编码，不可控
- ❌ 动作检测抽帧：实现复杂，Phase 1不需要
- ✅ 均匀抽帧：简单可靠，覆盖完整时间线

**Rationale**: 摔倒是连续动作（失去平衡→倒下→撞击→静止），均匀抽帧能捕捉完整过程。5帧足够判断时序模式。

### 3. 结果聚合：时序推理

**决策**: 基于帧序列的风险等级变化模式判断，而非简单投票。

**Alternatives considered:**
- ❌ 最高风险优先：容易误报（单帧异常即判定critical）
- ❌ 简单投票：丢失时序信息（无法区分"躺下"vs"摔倒"）
- ✅ 时序推理：识别"normal→warning→critical→critical"典型摔倒模式

**Rationale**: 摔倒的核心特征是"状态突变"，时序推理可以区分：
- 摔倒：站立→倾斜→倒地→静止（状态恶化）
- 躺下休息：站立→倾斜→躺下→静止（主动行为，但时序相似，需结合上下文）
- 坐下：站立→倾斜→坐下→静止（非critical状态）

### 4. API设计：独立事件触发端点

**决策**: 新增`/api_event_trigger`端点，而非修改现有`/api_planning`。

**Alternatives considered:**
- ❌ 复用`/api_planning`：语义不清晰，任务类型混杂
- ✅ 新端点：职责清晰，便于后续扩展传感器触发

**Rationale**: 事件触发（传感器/手动检查）与用户主动交互（对话）是不同场景，独立端点更符合REST设计原则。

### 5. 视频格式：支持多种格式

**决策**: 前端支持WebM、MP4、MOV、AVI上传，后端OpenCV统一解码。

**Rationale**: OpenCV支持主流视频格式，前端可根据浏览器能力选择格式（Chrome偏好WebM，Safari偏好MP4）。

## Risks / Trade-offs

### [风险1] Qwen-VL单帧分析误判
**风险**: 单帧可能将"躺椅休息"误判为"倒地"
**缓解**: 
- 时序推理要求至少3帧critical才判定摔倒
- 结合上下文（如时间段、历史记录）
- Phase 2引入视频专用模型

### [风险2] 视频文件大小
**风险**: 8秒视频可能达到2-5MB，影响传输速度
**缓解**:
- 前端限制分辨率（720p）和码率（1Mbps）
- 目标控制在1-1.5MB
- Phase 2考虑前端压缩

### [风险3] OpenCV依赖
**风险**: `opencv-python`增加Docker镜像大小（约60MB）
**缓解**: 
- 使用`opencv-python-headless`（无GUI，更小）
- 多阶段构建优化镜像

### [风险4] 时序推理准确性
**风险**: 均匀抽帧可能错过关键动作瞬间
**缓解**:
- 8秒5帧覆盖1.6秒间隔，摔倒动作通常持续2-3秒，至少捕获2帧
- Phase 2考虑自适应抽帧

## Migration Plan

### 部署步骤
1. 后端部署：
   - 安装`opencv-python-headless`和`numpy`
   - 部署新代码（vision.py、workflow、activities、API）
   - 更新Temporal Worker
   
2. 前端部署：
   - 更新Streamlit app.py
   - 添加视频上传测试页面

3. 验证：
   - 上传正常视频 → 验证normal结果
   - 上传摔倒模拟视频 → 验证critical结果
   - 对比图片检测vs视频检测的误报率

### 回滚策略
- 保留现有`/api_planning`和图片检测功能
- 新端点`/api_event_trigger`独立部署，不影响现有功能
- 如遇问题，可禁用新Workflow，回退到图片检测

## Open Questions

1. **报警机制**: 检测到摔倒后是否需要自动通知紧急联系人？（Phase 2决定）
2. **传感器对接**: 未来如何接收外部传感器触发信号？（HTTP Webhook / MQTT / 其他）
3. **性能优化**: 如果并发请求增多，是否需要GPU加速视频处理？
4. **隐私合规**: 视频存储策略是什么？是否需要加密？保留多久？
