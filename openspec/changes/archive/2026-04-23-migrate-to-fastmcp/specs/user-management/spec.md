## MODIFIED Requirements

### Requirement: 系统必须实现用户CRUD操作
系统 SHALL 使用 FastMCP 装饰器实现用户 CRUD 操作，通过 @mcp.tool() 自动注册工具，工具名称保持为 user.create_user、user.get_user、user.update_user、user.delete_user。

#### Scenario: 创建用户
- **WHEN** 调用 user.create_user 并提供 name、role、age 等必需字段
- **THEN** 系统创建用户并返回用户 ID

#### Scenario: 查询用户信息
- **WHEN** 调用 user.get_user 并提供 user_id
- **THEN** 系统返回用户完整信息

#### Scenario: 更新用户信息
- **WHEN** 调用 user.update_user 并提供更新的字段
- **THEN** 系统更新用户信息并返回更新后的用户数据

#### Scenario: 删除用户
- **WHEN** 调用 user.delete_user 并提供 user_id
- **THEN** 系统删除用户并返回确认信息

### Requirement: 系统必须支持用户切换
系统 SHALL 使用 FastMCP 装饰器实现用户切换功能，工具名称保持为 user.switch_user。

#### Scenario: 看护人切换用户
- **WHEN** 看护人调用 user.switch_user 并指定目标 user_id
- **THEN** 系统切换当前上下文到目标用户

### Requirement: 系统必须支持音色偏好设置
系统 SHALL 使用 FastMCP 装饰器实现音色偏好管理，工具名称保持为 user.set_voice_preference 和 user.get_voice_preference。

#### Scenario: 设置用户音色
- **WHEN** 调用 user.set_voice_preference 并提供 user_id 和 voice_id
- **THEN** 系统保存用户的音色偏好

#### Scenario: 获取用户音色
- **WHEN** 调用 user.get_voice_preference 并提供 user_id
- **THEN** 系统返回用户配置的音色 ID
