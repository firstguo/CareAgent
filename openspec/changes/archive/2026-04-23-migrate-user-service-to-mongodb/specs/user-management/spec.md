## REMOVED Requirements

### Requirement: 系统必须使用 Milvus 向量数据库存储用户信息
**Reason**: Milvus 是向量检索数据库，用户 CRUD 操作不需要向量能力。profile_vector 字段定义后从未使用，且 Milvus 的更新操作需要 delete + insert，导致功能实现受限。已迁移到 MongoDB 文档数据库。

**Migration**: 用户信息存储已迁移到 MongoDB，参见 user-mongodb-storage 规范。MCP 工具接口保持不变，内部实现从 pymilvus 改为 motor。
