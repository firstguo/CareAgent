## ADDED Requirements

### Requirement: 系统必须支持创建定时任务
系统 需要支持创建定时提醒任务，包含提醒时间、消息内容、重复规则等字段。

#### Scenario: 创建用药提醒
- **WHEN** 调用schedule.create_reminder并设置每天8:00提醒"吃降压药"
- **THEN** 系统创建定时任务并保存

#### Scenario: 创建单次提醒
- **WHEN** 调用schedule.create_reminder并设置特定时间点的一次性提醒
- **THEN** 系统创建单次任务

### Requirement: 系统必须支持任务CRUD操作
系统 需要支持定时任务的创建、查询、更新、删除操作。

#### Scenario: 查询用户的所有任务
- **WHEN** 调用schedule.list_tasks并提供user_id
- **THEN** 系统返回该用户的所有定时任务列表

#### Scenario: 更新任务
- **WHEN** 调用schedule.update_task修改提醒时间
- **THEN** 系统更新任务信息

#### Scenario: 删除任务
- **WHEN** 调用schedule.delete_task并提供task_id
- **THEN** 系统删除对应的定时任务

### Requirement: 系统必须支持任务启停控制
系统 需要支持启用和禁用定时任务，禁用后任务不会触发。

#### Scenario: 启用任务
- **WHEN** 调用schedule.enable_task并提供task_id
- **THEN** 系统激活该任务，到期时会触发

#### Scenario: 禁用任务
- **WHEN** 调用schedule.disable_task并提供task_id
- **THEN** 系统暂停该任务，到期不会触发

### Requirement: 系统必须支持重复规则
系统 需要支持多种重复规则：每天、每周、每月、工作日等。

#### Scenario: 创建每天重复任务
- **WHEN** 设置repeat为daily
- **THEN** 系统每天在指定时间触发任务

#### Scenario: 创建工作日重复任务
- **WHEN** 设置repeat为weekday
- **THEN** 系统仅在周一至周五触发任务
