## Context

当前 user-service 使用 Milvus 向量数据库存储用户信息，但实际只需要简单的 CRUD 操作。Milvus 的架构限制导致：
- 更新操作需要 delete + insert，无法实现原子更新
- profile_vector 向量字段从未使用，但占用存储和索引开销
- update_user、switch_user、set_voice_preference 等功能都是空壳实现

MongoDB 已在项目中运行（chat-service 用于任务状态存储），使用 motor 异步驱动。将 user-service 迁移到 MongoDB 可以：
- 简化架构，减少不必要的 Milvus 依赖
- 使用 MongoDB 原生更新操作补全缺失功能
- 与 chat-service 保持一致的技术栈

## Goals / Non-Goals

**Goals:**
- 将 user-service 的存储层从 Milvus 完全迁移到 MongoDB
- 保持现有 MCP 工具接口不变（对外透明）
- 补全所有空壳函数（update_user、switch_user、set_voice_preference 等）
- 使用 motor 异步驱动与 FastAPI 保持一致

**Non-Goals:**
- 不保留向量检索能力（profile_vector 字段彻底移除）
- 不进行数据迁移（开发阶段，Milvus 中无重要数据）
- 不改变 MCP 工具接口定义
- 不影响其他服务（chat-service 的 memory 模块如仍使用 Milvus 则不受影响）

## Decisions

### Decision 1: 使用 motor 而非 pymongo

**选择**: motor (AsyncIOMotorClient)

**理由**:
- FastAPI 是异步框架，motor 提供原生异步 API
- 与 chat-service 保持一致（chat-service 已使用 motor）
- 避免阻塞事件循环

**备选方案**: 
- pymongo（同步）：代码更简单，但在 FastAPI 中会阻塞事件循环

### Decision 2: 集合命名使用 `users`

**选择**: MongoDB 集合名为 `users`（而非沿用 Milvus 的 `careagent_users`）

**理由**:
- 简洁明了
- MongoDB 是独立数据库，不需要与 Milvus 区分命名空间
- 通过数据库名即可区分（如 `careagent.users`）

### Decision 3: 保留 user_id UUID 字段

**选择**: 继续使用 UUID 作为业务 user_id，MongoDB _id 作为内部主键

**理由**:
- 保持 MCP 接口兼容性
- UUID 适合分布式系统
- MongoDB _id 由数据库自动管理

**数据结构**:
```javascript
{
  _id: ObjectId,              // MongoDB 自动生成
  user_id: "uuid-string",     // 业务 ID (MCP 接口使用)
  name: "张三",
  role: "elder",              // elder | child | caregiver
  age: 75,
  health_info: {},            // JSON 对象
  preferences: {},            // JSON 对象
  voice_preference: "voice-001",
  created_at: "2026-04-23T10:00:00",
  updated_at: "2026-04-23T10:00:00"
}
```

### Decision 4: 使用 $set 操作实现更新

**选择**: MongoDB `$set` 操作符实现部分更新

**理由**:
- 支持原子更新
- 只更新提供的字段，不影响其他字段
- 自动更新 updated_at 时间戳

**实现**:
```python
await collection.update_one(
    {"user_id": user_id},
    {"$set": {**update_data, "updated_at": now}}
)
```

### Decision 5: 索引策略

**选择**: 仅为 user_id 创建唯一索引

**理由**:
- user_id 是主要查询字段
- 唯一索引保证数据一致性
- 其他字段查询频率低，不需要额外索引

## Risks / Trade-offs

| Risk | Impact | Mitigation |
|------|--------|------------|
| Milvus 实例是否可移除 | 如果 chat-service 的 memory 模块仍使用 Milvus，则不能移除 | 迁移后检查 Milvus 使用情况，如无人使用再移除 |
| motor 版本兼容性 | motor 版本与 MongoDB 版本不匹配可能导致问题 | 使用 motor 3.3.2（与 MongoDB 7.0 兼容） |
| 服务启动顺序 | user-service 需要在 MongoDB 启动后启动 | docker-compose.yml 中添加 depends_on: mongodb |
| 空壳函数实现不完整 | switch_user 等业务逻辑可能缺少上下文 | 当前版本返回简单确认，后续可根据需求增强 |

## Migration Plan

### 部署步骤
1. 更新 user-service 代码和依赖
2. 更新 docker-compose.yml 配置
3. 重建并重启 user-service 容器
4. 验证 MongoDB 连接和 CRUD 操作
5. 测试所有 MCP 工具接口

### 回滚策略
- 保留 Milvus 实例直到验证完成
- 如需回滚，恢复旧版 user-service 代码和依赖
- MongoDB 中的用户数据不影响回滚（Milvus 和 MongoDB 独立）

### 验证清单
- [ ] user-service 成功连接 MongoDB
- [ ] user.create_user 创建用户并返回 user_id
- [ ] user.get_user 查询用户信息
- [ ] user.update_user 更新用户信息
- [ ] user.delete_user 删除用户
- [ ] user.set_voice_preference 设置音色偏好
- [ ] user.get_voice_preference 获取音色偏好
- [ ] user.switch_user 切换用户
- [ ] MongoDB users 集合索引正确创建

## Open Questions

无。所有设计决策已明确。
