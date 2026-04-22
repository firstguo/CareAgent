## ADDED Requirements

### Requirement: 系统必须使用MLflow追踪AI实验
系统 需要使用MLflow记录每次LLM调用的参数、结果、Token消耗等信息，支持实验对比。

#### Scenario: 记录LLM调用
- **WHEN** LLM服务发起一次对话请求
- **THEN** 系统在MLflow记录model、temperature、tokens、cost等信息

#### Scenario: 查询实验记录
- **WHEN** 访问MLflow UI
- **THEN** 可查看历史实验和指标对比

### Requirement: 系统必须暴露Prometheus指标
每个MCP Server 需要在/metrics端点提供Prometheus格式的指标数据。

#### Scenario: 获取LLM服务指标
- **WHEN** 访问http://llm-service:8005/metrics
- **THEN** 返回请求数、延迟、Token消耗等指标

### Requirement: 系统必须提供Grafana仪表盘
系统 需要配置Grafana Dashboard，可视化展示系统运行状态。

#### Scenario: 查看服务健康状态
- **WHEN** 访问http://localhost:3000
- **THEN** 显示各服务的健康状态、QPS、延迟等面板

#### Scenario: 查看Token消耗
- **WHEN** 打开Token监控面板
- **THEN** 显示各模型的Token消耗和成本统计

### Requirement: 系统必须记录详细日志
每个服务 需要记录结构化日志，包含请求ID、用户ID、耗时等字段。

#### Scenario: 记录请求日志
- **WHEN** 处理一次LLM请求
- **THEN** 日志记录request_id、user_id、duration、tokens等信息

#### Scenario: 记录错误日志
- **WHEN** 服务发生异常
- **THEN** 日志记录error_type、stack_trace、context等详细信息
