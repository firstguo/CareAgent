## ADDED Requirements

### Requirement: 系统需要使用LangChain框架
系统 需要使用LangChain框架构建LLM应用，利用其Chain、Agent、Memory等核心组件，统一管理大模型调用。

#### Scenario: 使用LangChain调用通义千问
- **WHEN** LLM服务初始化
- **THEN** 系统使用LangChain的ChatOpenAI兼容接口连接通义千问

#### Scenario: 使用Prompt模板
- **WHEN** 发起对话请求
- **THEN** 系统使用LangChain的PromptTemplate管理System Prompt

### Requirement: 系统必须支持对话生成
系统 需要集成通义千问大模型，支持单轮和多轮对话，返回文本回复。

#### Scenario: 单轮对话
- **WHEN** 调用llm.chat提供用户输入
- **THEN** 系统返回LLM生成的回复

#### Scenario: 多轮对话
- **WHEN** 调用llm.chat并提供对话历史
- **THEN** 系统基于上下文生成回复

### Requirement: 系统必须支持流式输出
系统 需要支持流式对话输出，逐步返回生成的token，提升用户体验。

#### Scenario: 流式对话
- **WHEN** 调用llm.chat_stream并提供用户输入
- **THEN** 系统逐步返回生成的token

### Requirement: 系统必须启用Prefix Cache
系统 需要在LLM请求中启用Prefix Cache，对System Prompt和用户档案使用显式缓存标记，降低Token成本。

#### Scenario: 创建缓存
- **WHEN** 首次发起对话，System Prompt超过1024 tokens
- **THEN** 系统创建Prefix Cache并返回cache_creation_input_tokens

#### Scenario: 命中缓存
- **WHEN** 再次发起对话，System Prompt相同
- **THEN** 系统命中缓存，返回cached_tokens

### Requirement: 系统必须实现分级模型路由
系统 需要根据意图识别结果选择合适的模型：简单问题使用Qwen-Turbo，复杂分析使用Qwen-Max，一般对话使用Qwen-Plus。

#### Scenario: 简单问题路由到Turbo
- **WHEN** 用户询问"今天天气如何"
- **THEN** 系统使用Qwen-Turbo模型

#### Scenario: 复杂问题路由到Max
- **WHEN** 用户描述"爷爷头晕且血压偏高"
- **THEN** 系统使用Qwen-Max模型

### Requirement: 系统必须支持文本摘要
系统 需要提供文本摘要功能，用于对话历史压缩和记忆摘要。

#### Scenario: 摘要长文本
- **WHEN** 调用llm.summarize提供长文本
- **THEN** 系统返回简洁的摘要

### Requirement: 系统必须支持意图识别
系统 需要识别用户输入的意图，支持问答、紧急、闲聊、指令等类型。

#### Scenario: 识别问答意图
- **WHEN** 用户输入"爷爷该吃什么药"
- **THEN** 系统识别为medication_query意图

#### Scenario: 识别紧急意图
- **WHEN** 用户输入"我摔倒了"
- **THEN** 系统识别为emergency意图
