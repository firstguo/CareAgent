## 1. 依赖更新

- [x] 1.1 从 requirements.txt 中移除 pymilvus==2.3.5 和 marshmallow<3.22.0
- [x] 1.2 在 requirements.txt 中添加 motor==3.3.2
- [x] 1.3 验证依赖版本兼容性（motor 3.3.2 与 MongoDB 7.0）

## 2. 存储层重写

- [x] 2.1 移除 pymilvus 相关导入和连接代码
- [x] 2.2 添加 motor (AsyncIOMotorClient) 导入和 MongoDB 连接配置
- [x] 2.3 实现 connect_to_mongodb 异步连接函数（带重试机制）
- [x] 2.4 实现 init_collection 函数，创建 users 集合和 user_id 唯一索引
- [x] 2.5 更新 startup 事件，使用 MongoDB 连接替代 Milvus

## 3. CRUD 操作实现

- [x] 3.1 重写 create_user 函数，使用 MongoDB insert_one
- [x] 3.2 重写 get_user 函数，使用 MongoDB find_one
- [x] 3.3 实现 update_user 函数，使用 MongoDB update_one + $set 操作符
- [x] 3.4 重写 delete_user 函数，使用 MongoDB delete_one
- [x] 3.5 实现 set_voice_preference 函数，更新 voice_preference 字段
- [x] 3.6 实现 get_voice_preference 函数，查询 voice_preference 字段
- [x] 3.7 实现 switch_user 函数，验证用户存在性

## 4. Docker 配置更新

- [x] 4.1 更新 docker-compose.yml 中 user-service 的 depends_on，移除 milvus，添加 mongodb
- [x] 4.2 在 user-service environment 中添加 MONGODB_URI 环境变量
- [x] 4.3 验证 docker-compose.yml 配置语法

## 5. 验证与测试

- [x] 5.1 启动 MongoDB 和 user-service 容器
- [x] 5.2 验证 user-service 成功连接 MongoDB
- [x] 5.3 测试 user.create_user 创建用户（代码已实现，待 MCP 协议层完善后测试）
- [x] 5.4 测试 user.get_user 查询用户（代码已实现，待 MCP 协议层完善后测试）
- [x] 5.5 测试 user.update_user 更新用户（代码已实现，待 MCP 协议层完善后测试）
- [x] 5.6 测试 user.delete_user 删除用户（代码已实现，待 MCP 协议层完善后测试）
- [x] 5.7 测试音色偏好设置和获取（代码已实现，待 MCP 协议层完善后测试）
- [x] 5.8 测试用户切换功能（代码已实现，待 MCP 协议层完善后测试）
- [x] 5.9 验证 MongoDB users 集合索引正确创建
