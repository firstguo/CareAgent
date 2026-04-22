## ADDED Requirements

### Requirement: 系统必须支持记忆存储
系统 需要使用Mem0 + Milvus存储用户记忆，支持事实记忆、偏好记忆、事件记忆三种类型。

#### Scenario: 添加事实记忆
- **WHEN** 调用memory.add添加"爷爷有高血压"
- **THEN** 系统将记忆向量化并存储到Milvus

#### Scenario: 添加事件记忆
- **WHEN** 调用memory.add添加"2024-01-15爷爷头晕"
- **THEN** 系统存储事件记忆并关联时间戳

### Requirement: 系统必须支持语义检索记忆
系统 需要根据查询内容检索相关记忆，返回按相关性排序的记忆列表，支持Top-K参数控制返回数量。

#### Scenario: 检索健康相关记忆
- **WHEN** 调用memory.search查询"爷爷的健康状况"
- **THEN** 系统返回高血压、头晕等相关记忆

#### Scenario: 限制检索数量
- **WHEN** 调用memory.search并设置top_k=3
- **THEN** 系统返回最相关的3条记忆

### Requirement: 系统必须支持记忆更新和删除
系统 需要支持记忆的更新和删除操作，确保记忆的准确性和时效性。

#### Scenario: 更新记忆
- **WHEN** 调用memory.update修改记忆内容
- **THEN** 系统更新记忆并重新向量化

#### Scenario: 删除记忆
- **WHEN** 调用memory.delete指定memory_id
- **THEN** 系统从Milvus中删除对应记忆

### Requirement: 系统必须支持对话历史查询
系统 需要存储和检索用户的对话历史，支持按时间范围和关键词查询。

#### Scenario: 获取最近对话历史
- **WHEN** 调用memory.get_conversation_history并提供user_id
- **THEN** 系统返回最近的对话记录

### Requirement: 系统必须支持用户画像摘要
系统 需要根据记忆生成用户画像摘要，包含健康状况、偏好、重要事件等信息。

#### Scenario: 获取用户画像
- **WHEN** 调用memory.get_user_profile并提供user_id
- **THEN** 系统返回用户画像摘要
