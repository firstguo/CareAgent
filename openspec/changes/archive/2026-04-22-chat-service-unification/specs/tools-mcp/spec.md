## ADDED Requirements

### Requirement: tools-mcp必须提供Web搜索能力
tools-mcp SHALL集成TAVILY API，提供互联网信息搜索功能。

#### Scenario: 执行Web搜索
- **WHEN** 客户端调用tools.web_search工具，传入查询关键词
- **THEN** 系统调用TAVILY API，返回相关搜索结果摘要

#### Scenario: 搜索实时新闻
- **WHEN** 用户询问"今天有什么重要新闻"
- **THEN** tools.web_search返回最新的新闻摘要和来源链接

### Requirement: tools-mcp必须提供地址信息查询能力
tools-mcp SHALL集成AMAP（高德地图）API，提供地理位置查询服务。

#### Scenario: 查询地点信息
- **WHEN** 客户端调用tools.location_query工具，传入地点名称
- **THEN** 系统调用AMAP API，返回地址、坐标、电话号码等信息

#### Scenario: 搜索附近设施
- **WHEN** 用户询问"附近有哪些药店"
- **THEN** tools.location_query返回附近药店的列表，包含名称、地址、距离

### Requirement: tools-mcp必须作为独立MCP Server部署
tools-mcp SHALL作为独立的Docker容器部署，提供MCP协议接口。

#### Scenario: tools-mcp服务启动
- **WHEN** 执行docker-compose up
- **THEN** tools-mcp服务启动在端口8008

#### Scenario: Gateway路由tools请求
- **WHEN** 客户端调用tools.web_search或tools.location_query
- **THEN** Gateway将请求路由到tools-mcp:8008

### Requirement: tools-mcp必须配置外部API密钥
tools-mcp SHALL通过环境变量配置TAVILY和AMAP的API密钥。

#### Scenario: 配置TAVILY API密钥
- **WHEN** tools-mcp启动
- **THEN** 读取TAVILY_API_KEY环境变量

#### Scenario: 配置AMAP API密钥
- **WHEN** tools-mcp启动
- **THEN** 读取AMAP_API_KEY环境变量
