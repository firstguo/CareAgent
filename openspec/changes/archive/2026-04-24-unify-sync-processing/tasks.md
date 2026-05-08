## 1. 统一同步入口

- [x] 1.1 修改 `/api_planning` 路由，移除异步任务分发
- [x] 1.2 实现统一入口函数，根据 input.type 路由
- [x] 1.3 移除 `handle_async_task` 函数（保留但不再调用）
- [x] 1.4 移除 `api_task_status` 端点（保留但不再使用）

## 2. 视频预先检测

- [x] 2.1 添加视频检测函数调用入口
- [x] 2.2 实现风险等级判断逻辑（normal vs critical/warning）
- [x] 2.3 实现 `format_detection_as_text()` 函数
- [x] 2.4 添加检测结果日志记录

## 3. 忽略模式实现

- [x] 3.1 实现 ignored 模式响应格式
- [x] 3.2 非危险视频直接返回，不调 LLM
- [x] 3.3 非危险视频不创建 session
- [ ] 3.4 测试 ignored 模式响应（需要运行时测试）

## 4. 危险视频对话化

- [x] 4.1 危险视频生成文本描述
- [x] 4.2 调用 `handle_conversation` 处理危险事件
- [x] 4.3 创建新 session（独立危险事件会话）
- [ ] 4.4 测试危险视频完整流程（需要运行时测试）

## 5. 语音输入优化

- [x] 5.1 确认语音 ASR 转文字逻辑
- [x] 5.2 转文字后调用 `handle_conversation`
- [x] 5.3 添加 ASR 耗时日志

## 6. 前端适配

- [x] 6.1 移除轮询逻辑（`pollTaskStatus`）
- [x] 6.2 处理 `conversation` 模式响应
- [x] 6.3 处理 `ignored` 模式响应
- [x] 6.4 添加加载提示（"正在分析视频..."）
- [x] 6.5 测试文本/语音/视频输入（代码实现）

## 7. 清理异步代码

- [x] 7.1 移除 `execute_task` 函数调用
- [x] 7.2 移除 MongoDB tasks 集合写入
- [x] 7.3 清理 `handle_async_task` 相关依赖
- [x] 7.4 更新 API 文档

## 8. 监控和测试

- [ ] 8.1 添加视频检测耗时监控
- [ ] 8.2 统计 ignored/conversation 比例
- [ ] 8.3 端到端测试所有输入类型
- [ ] 8.4 压力测试并发视频处理
