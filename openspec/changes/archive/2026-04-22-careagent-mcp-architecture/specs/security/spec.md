## ADDED Requirements

### Requirement: 系统必须实现JWT认证
系统 需要使用RS256非对称加密算法签发和验证JWT Token，包含用户ID、角色、过期时间等信息。

#### Scenario: 签发Token
- **WHEN** 用户登录成功
- **THEN** 系统返回JWT Token，有效期24小时

#### Scenario: 验证Token
- **WHEN** 请求携带JWT Token访问受保护资源
- **THEN** Gateway验证Token签名和有效期

### Requirement: 系统必须实现基于角色的权限控制
系统 需要根据用户角色(elder/child/caregiver)限制可访问的资源和操作。

#### Scenario: 老年人访问权限
- **WHEN** 老年人用户调用对话服务
- **THEN** 系统允许访问llm.*和memory.*工具

#### Scenario: 看护人管理权限
- **WHEN** 看护人用户调用用户管理工具
- **THEN** 系统允许访问user.*所有工具

### Requirement: 系统必须过滤恶意Prompt
系统 需要使用正则表达式检测并过滤Prompt注入攻击，包含15+种攻击模式。

#### Scenario: 检测角色扮演注入
- **WHEN** 用户输入包含"忽略之前的指令，你是X"
- **THEN** 系统拒绝请求并返回安全警告

#### Scenario: 检测代码注入
- **WHEN** 用户输入包含"<script>"或SQL关键字
- **THEN** 系统拒绝请求并记录安全事件

### Requirement: 系统必须实施速率限制
系统 需要对每个用户和全局实施速率限制，防止API滥用。

#### Scenario: 用户LLM请求限流
- **WHEN** 用户1分钟内发起超过30次LLM请求
- **THEN** 系统拒绝后续请求并返回429错误

#### Scenario: 全局限流
- **WHEN** 全局请求超过设定阈值
- **THEN** 系统拒绝新请求直到窗口重置

### Requirement: 系统必须保护敏感配置
系统 需要加密存储API Key、JWT密钥等敏感信息，禁止硬编码。

#### Scenario: 加密API Key
- **WHEN** 系统启动时加载.env文件
- **THEN** API Key在内存中解密使用，不在日志中暴露

#### Scenario: 密钥文件权限
- **WHEN** 检查keys目录权限
- **THEN** 私钥文件权限为600，仅owner可读写
