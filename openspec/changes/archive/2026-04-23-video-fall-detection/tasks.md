## 1. 依赖管理

- [x] 1.1 在services/chat-service/requirements.txt中添加opencv-python-headless和numpy依赖
- [x] 1.2 更新Dockerfile安装新依赖（如需要）

## 2. 视频处理核心实现

- [x] 2.1 在modules/vision.py中实现extract_frames_uniform函数（OpenCV视频解码+均匀抽帧）
- [x] 2.2 在modules/vision.py中实现aggregate_temporal_results函数（时序推理聚合）
- [x] 2.3 在modules/vision.py中实现analyze_temporal_pattern函数（时序模式识别）
- [x] 2.4 在modules/vision.py中实现generate_recommendations函数（分级建议生成）
- [x] 2.5 在modules/vision.py中实现detect_danger_video主函数（整合解码-抽帧-分析-聚合流程）

## 3. Temporal Activity和Workflow

- [x] 3.1 在activities/task_activities.py中新增vision_detect_danger_video Activity
- [x] 3.2 在worker.py中注册新Activity到Worker
- [x] 3.3 在workflows/care_task_workflow.py中新增VideoFallDetectionWorkflow类
- [x] 3.4 在workflows/__init__.py中导出新Workflow

## 4. API端点和数据模型

- [x] 4.1 在main.py中扩展InputData模型，添加video类型和video_data字段
- [x] 4.2 在main.py中新增EventTriggerInput和VideoAnalysisResult数据模型
- [x] 4.3 在main.py中实现POST /api_event_trigger端点
- [x] 4.4 在main.py的startup事件中确认MongoDB索引支持视频类型（已足够，无需修改）

## 5. 前端测试页面

- [x] 5.1 在frontend/app.py中新增视频上传测试区域
- [x] 5.2 实现视频文件上传和Base64编码逻辑
- [x] 5.3 实现调用/api_event_trigger并轮询结果的逻辑
- [x] 5.4 实现结果展示（风险等级、置信度、时序证据、建议措施）
- [x] 5.5 添加帧分析详情折叠面板

## 6. 测试和验证

- [ ] 6.1 准备测试视频集（正常行走、坐下、摔倒模拟、躺下休息）
- [ ] 6.2 测试视频上传和后端接收
- [ ] 6.3 测试视频解码和抽帧功能
- [ ] 6.4 测试时序推理聚合逻辑
- [ ] 6.5 端到端测试：上传视频→查看结果→验证准确性
- [ ] 6.6 对比测试：同一场景图片检测vs视频检测的误报率
