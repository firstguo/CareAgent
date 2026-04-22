## ADDED Requirements

### Requirement: 系统必须支持三类用户角色
系统 需要支持老年人(elder)、小朋友(child)、看护人(caregiver)三种角色，每种角色具有不同的权限和行为模式。

#### Scenario: 创建老年人用户
- **WHEN** 创建用户并设置role为elder
- **THEN** 系统创建老年人用户，应用老年人交互模式

#### Scenario: 创建小朋友用户
- **WHEN** 创建用户并设置role为child
- **THEN** 系统创建小朋友用户，应用小朋友交互模式

#### Scenario: 创建看护人用户
- **WHEN** 创建用户并设置role为caregiver
- **THEN** 系统创建看护人用户，应用看护人交互模式和管理权限

### Requirement: 系统必须实现用户CRUD操作
系统 需要支持用户的创建、查询、更新、删除操作，包含基本信息、角色、健康信息、偏好设置等字段。

#### Scenario: 创建用户
- **WHEN** 调用user.create_user并提供name、role、age等必需字段
- **THEN** 系统创建用户并返回用户ID

#### Scenario: 查询用户信息
- **WHEN** 调用user.get_user并提供user_id
- **THEN** 系统返回用户完整信息

#### Scenario: 更新用户信息
- **WHEN** 调用user.update_user并提供更新的字段
- **THEN** 系统更新用户信息并返回更新后的用户数据

### Requirement: 系统必须支持用户切换
系统 需要允许看护人角色在多个被看护用户之间切换，切换后所有操作针对当前选中的用户。

#### Scenario: 看护人切换用户
- **WHEN** 看护人调用user.switch_user并指定目标user_id
- **THEN** 系统切换当前上下文到目标用户

### Requirement: 系统必须支持音色偏好设置
系统 需要允许每个用户设置独立的音色偏好，用于TTS语音合成。

#### Scenario: 设置用户音色
- **WHEN** 调用user.set_voice_preference并提供user_id和voice_id
- **THEN** 系统保存用户的音色偏好

#### Scenario: 获取用户音色
- **WHEN** 调用user.get_voice_preference并提供user_id
- **THEN** 系统返回用户配置的音色ID
