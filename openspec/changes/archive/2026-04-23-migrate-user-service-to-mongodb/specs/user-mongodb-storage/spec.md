## ADDED Requirements

### Requirement: 系统必须使用 MongoDB 存储用户信息
系统 SHALL 使用 MongoDB 文档数据库存储所有用户信息，集合名称为 `users`。每个用户文档 MUST 包含 user_id（UUID 格式）、name、role、age、health_info、preferences、voice_preference、created_at、updated_at 字段。

#### Scenario: 用户文档创建
- **WHEN** 调用用户创建接口
- **THEN** 系统在 MongoDB 的 users 集合中插入新文档，自动生成 _id 和业务 user_id

#### Scenario: 用户文档结构
- **WHEN** 查询用户文档
- **THEN** 文档包含所有必需字段，health_info 和 preferences 为 JSON 对象

### Requirement: 系统必须使用 motor 异步驱动连接 MongoDB
系统 SHALL 使用 motor (AsyncIOMotorClient) 异步驱动连接 MongoDB，以与 FastAPI 异步框架保持一致。连接字符串 MUST 从环境变量 MONGODB_URI 读取。

#### Scenario: 服务启动时连接 MongoDB
- **WHEN** user-service 启动
- **THEN** 系统使用 motor 异步连接到 MongoDB，并获取 users 集合引用

#### Scenario: 连接失败重试
- **WHEN** MongoDB 连接失败
- **THEN** 系统记录错误日志并重试，最多重试 30 次，间隔 2 秒

### Requirement: 系统必须实现完整的用户 CRUD 操作
系统 SHALL 提供完整的创建、读取、更新、删除用户功能，所有操作 MUST 通过 MongoDB 原生 API 实现。

#### Scenario: 创建用户
- **WHEN** 调用 user.create_user 提供 name、role 等字段
- **THEN** 系统生成 UUID 作为 user_id，插入 MongoDB 文档，返回 user_id

#### Scenario: 查询用户
- **WHEN** 调用 user.get_user 提供 user_id
- **THEN** 系统通过 user_id 索引查询 MongoDB，返回用户完整信息；如用户不存在返回错误提示

#### Scenario: 更新用户
- **WHEN** 调用 user.update_user 提供 user_id 和需要更新的字段
- **THEN** 系统使用 MongoDB $set 操作更新指定字段，更新 updated_at 时间戳，返回更新后的用户数据

#### Scenario: 删除用户
- **WHEN** 调用 user.delete_user 提供 user_id
- **THEN** 系统从 MongoDB 中删除对应用户文档，返回删除确认信息

### Requirement: 系统必须为 user_id 创建唯一索引
系统 SHALL 在 MongoDB 的 users 集合上为 user_id 字段创建唯一索引，以确保用户 ID 的唯一性并加速查询。

#### Scenario: 集合初始化时创建索引
- **WHEN** user-service 启动并初始化集合
- **THEN** 系统为 user_id 字段创建唯一索引，如索引已存在则跳过

### Requirement: 系统必须支持音色偏好管理
系统 SHALL 提供设置和获取用户音色偏好的功能，音色偏好存储在用户文档的 voice_preference 字段中。

#### Scenario: 设置音色偏好
- **WHEN** 调用 user.set_voice_preference 提供 user_id 和 voice_id
- **THEN** 系统更新用户文档的 voice_preference 字段和 updated_at

#### Scenario: 获取音色偏好
- **WHEN** 调用 user.get_voice_preference 提供 user_id
- **THEN** 系统查询用户文档并返回 voice_preference 字段值；如用户不存在返回错误提示

### Requirement: 系统必须支持用户切换功能
系统 SHALL 提供用户切换功能，允许看护人在多个被看护用户之间切换当前操作上下文。

#### Scenario: 切换用户
- **WHEN** 调用 user.switch_user 提供目标 user_id
- **THEN** 系统验证目标用户存在，返回切换成功信息；如用户不存在返回错误提示
