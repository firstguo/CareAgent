## Why

当前的摔倒检测基于静态图片分析，误报率较高（如将老人躺椅休息误判为摔倒）。通过引入视频时序分析，可以捕捉动作的连续性（站立→倾斜→倒地），大幅提升检测准确性，降低误报率80%以上，为照顾者提供更可靠的紧急通知。

## What Changes

- 新增视频摔倒检测能力，支持前端上传视频文件进行分析
- 后端实现视频解码、均匀抽帧、逐帧分析、时序推理聚合
- 新增Temporal Workflow编排视频检测流程
- 新增事件触发API端点 `/api_event_trigger`
- 前端Streamlit添加视频上传测试页面
- 保留现有图片检测能力（向后兼容）

## Capabilities

### New Capabilities
- `video-fall-detection`: 视频摔倒检测能力，包括视频解码、抽帧、时序分析和结果聚合

### Modified Capabilities
- `vision-service`: 扩展危险检测能力，新增视频输入支持（原有图片检测保持不变）

## Impact

- **受影响代码**: 
  - `services/chat-service/modules/vision.py` - 新增视频处理函数
  - `services/chat-service/activities/task_activities.py` - 新增视频检测Activity
  - `services/chat-service/workflows/care_task_workflow.py` - 新增VideoFallDetectionWorkflow
  - `services/chat-service/main.py` - 新增API端点和数据模型
  - `frontend/app.py` - 新增视频上传测试页面
  
- **新增依赖**: 
  - `opencv-python` (视频解码)
  - `numpy` (帧处理)
  
- **API变更**: 
  - 新增 `POST /api_event_trigger` 端点
  - `InputData` 模型扩展支持 `video` 类型

- **存储**: MongoDB任务记录扩展支持视频类型输入
