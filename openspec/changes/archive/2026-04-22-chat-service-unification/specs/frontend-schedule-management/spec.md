## ADDED Requirements

### Requirement: 前端必须在localStorage存储定时任务配置
当LLM识别到定时任务意图时，前端SHALL将任务配置保存到浏览器localStorage。

#### Scenario: 保存用药提醒任务
- **WHEN** 用户说"每天早上8点提醒我吃药"，LLM返回should_save_schedule=true
- **THEN** 前端在localStorage存储：{type: "medication_reminder", cron: "0 8 * * *", message: "提醒吃药"}

#### Scenario: 加载已有定时任务
- **WHEN** 前端页面初始化
- **THEN** 从localStorage读取careagent_schedules数组

### Requirement: 前端必须使用JS定时器检查并触发定时任务
前端SHALL每分钟检查一次localStorage中的任务，到达触发时间时调用Chat Service。

#### Scenario: 定时器触发任务
- **WHEN** 当前时间匹配任务的cron表达式（8:00 AM匹配"0 8 * * *"）
- **THEN** 前端POST /api_planning，trigger_type为"scheduled"

#### Scenario: 避免同一分钟重复触发
- **WHEN** 任务在8:00已触发
- **THEN** 8:00-8:59之间不再触发，更新last_triggered时间戳

### Requirement: 前端必须监听页面可见性变化
前端SHALL监听visibilitychange事件，页面回到前台时立即检查任务。

#### Scenario: 页面从后台回到前台
- **WHEN** 用户切换回浏览器标签页
- **THEN** 立即执行checkAndTrigger检查是否有待触发任务

#### Scenario: 页面持续后台运行
- **WHEN** 用户切换到其他App（手机端）
- **THEN** JS定时器可能暂停，回到前台时补偿检查

### Requirement: 前端必须在任务触发后播放语音回复
当Chat Service返回任务结果时，前端SHALL播放语音并显示文本。

#### Scenario: 播放定时任务语音提醒
- **WHEN** /api_planning返回completed状态，包含audio_response
- **THEN** 前端使用Audio API播放Base64编码的语音数据

#### Scenario: 震动提醒（Android设备）
- **WHEN** 定时任务触发且设备支持vibrate API
- **THEN** 执行navigator.vibrate([200, 100, 200])震动提醒

### Requirement: 前端必须提示用户保持页面打开
首次访问时，前端SHALL提示用户定时任务需要保持页面打开才能触发。

#### Scenario: 显示提示消息
- **WHEN** 用户首次访问应用
- **THEN** 显示Toast："为保证定时提醒正常工作，请保持页面打开"

#### Scenario: 移动端优化提示
- **WHEN** 检测到移动端浏览器
- **THEN** 提示"建议将手机屏幕保持常亮，或将页面添加到桌面"
