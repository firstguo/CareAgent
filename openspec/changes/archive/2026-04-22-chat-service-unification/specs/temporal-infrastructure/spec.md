## ADDED Requirements

### Requirement: 必须部署Temporal Server作为工作流引擎
系统SHALL在docker-compose中部署Temporal Server，提供工作流编排能力。

#### Scenario: Temporal Server启动
- **WHEN** 执行docker-compose up
- **THEN** temporal服务启动在端口7233

#### Scenario: Temporal自动初始化数据库
- **WHEN** Temporal Server首次启动
- **THEN** auto-setup镜像自动创建PostgreSQL数据库和表结构

### Requirement: 必须部署Temporal UI用于监控
系统SHALL部署Temporal Web UI，支持查看工作流执行状态、历史、重试记录。

#### Scenario: 访问Temporal UI
- **WHEN** 访问http://localhost:8080
- **THEN** 显示Temporal Web界面，可查看所有Workflow

#### Scenario: 查看工作流详情
- **WHEN** 点击某个CareTaskWorkflow
- **THEN** 显示执行步骤、时间线、输入输出、错误信息

### Requirement: 必须部署MongoDB用于任务状态存储
系统SHALL在docker-compose中部署MongoDB，提供任务状态持久化。

#### Scenario: MongoDB启动
- **WHEN** 执行docker-compose up
- **THEN** mongodb服务启动在端口27017

#### Scenario: MongoDB健康检查
- **WHEN** 执行mongosh --eval "db.adminCommand('ping')"
- **THEN** 返回ok: 1

### Requirement: 必须部署PostgreSQL用于Temporal元数据
系统SHALL部署PostgreSQL数据库，专门存储Temporal Server的元数据。

#### Scenario: PostgreSQL启动
- **WHEN** 执行docker-compose up
- **THEN** temporal-db服务启动，数据库名为temporal

#### Scenario: Temporal连接PostgreSQL
- **WHEN** Temporal Server启动
- **THEN** 自动连接temporal-db:5432，创建必要表结构

### Requirement: Chat Service必须配置Temporal和MongoDB连接
chat-service SHALL通过环境变量配置Temporal Server和MongoDB连接。

#### Scenario: 配置Temporal连接
- **WHEN** chat-service启动
- **THEN** 读取TEMPORAL_HOST=temporal:7233环境变量，建立连接

#### Scenario: 配置MongoDB连接
- **WHEN** chat-service启动
- **THEN** 读取MONGODB_URI=mongodb://admin:admin123@mongodb:27017环境变量，建立连接

#### Scenario: 依赖基础设施服务
- **WHEN** 执行docker-compose up
- **THEN** chat-service在temporal和mongodb健康检查通过后才启动
