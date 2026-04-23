## MODIFIED Requirements

### Requirement: 系统必须提供 Web 搜索工具
系统 SHALL 使用 FastMCP 装饰器实现 Web 搜索工具，工具名称保持为 tools.web_search，通过 TAVILY API 搜索实时信息。

#### Scenario: 执行 Web 搜索
- **WHEN** 调用 tools.web_search 并提供 query 参数
- **THEN** 系统返回搜索结果列表

#### Scenario: 自定义搜索结果数量
- **WHEN** 调用 tools.web_search 并提供 max_results 参数
- **THEN** 系统返回指定数量的搜索结果

### Requirement: 系统必须提供地址查询工具
系统 SHALL 使用 FastMCP 装饰器实现地址查询工具，工具名称保持为 tools.geocode，通过高德地图 API 进行地理编码。

#### Scenario: 地址地理编码
- **WHEN** 调用 tools.geocode 并提供 address 参数
- **THEN** 系统返回经纬度坐标信息

### Requirement: 系统必须提供天气查询工具
系统 SHALL 使用 FastMCP 装饰器实现天气查询工具，工具名称保持为 tools.weather，通过高德地图 API 查询实时天气。

#### Scenario: 查询城市天气
- **WHEN** 调用 tools.weather 并提供 city 参数
- **THEN** 系统返回当前天气信息
