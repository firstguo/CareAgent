## Why

当前 user-service 使用 Milvus（向量数据库）存储用户信息，但用户 CRUD 操作并不需要向量检索能力。`profile_vector` 字段定义后从未使用，且 Milvus 的更新操作需要 delete + insert，导致 `update_user` 等功能无法正确实现。MongoDB 已在项目中运行（chat-service 用于任务状态存储），迁移到 MongoDB 可以简化架构、提升可维护性，并补全缺失的用户管理功能。

## What Changes

- 将 user-service 的数据存储从 Milvus 迁移到 MongoDB
- 移除 Milvus 相关依赖（pymilvus、marshmallow）
- 添加 MongoDB 异步驱动（motor）
- 重写所有用户 CRUD 操作，使用 MongoDB 原生 API
- 补全 `update_user`、`switch_user`、`set_voice_preference` 等空壳函数
- 更新 docker-compose.yml 配置，将 user-service 依赖从 milvus 改为 mongodb

## Capabilities

### New Capabilities
- `user-mongodb-storage`: 用户信息 MongoDB 存储能力，包括用户 CRUD、音色偏好管理、用户切换等功能

### Modified Capabilities
- `user-management`: 用户管理服务的存储层实现从向量数据库改为文档数据库，接口保持不变

## Impact

**受影响的服务**:
- `services/user-service/main.py` - 完全重写存储层
- `services/user-service/requirements.txt` - 依赖变更
- `docker-compose.yml` - user-service 依赖配置更新

**API 影响**:
- MCP 工具接口保持不变（`user.create_user`、`user.get_user` 等）
- 内部实现完全替换，对外透明

**依赖影响**:
- user-service 不再依赖 milvus
- user-service 新增 mongodb 依赖
- Milvus 实例是否可移除取决于其他服务（chat-service 的 memory 模块可能仍在使用）
