## ADDED Requirements

### Requirement: 系统必须支持图像内容分析
系统 需要集成Qwen-VL视觉模型，分析图像内容并返回描述，支持人物状态、环境安全等场景。

#### Scenario: 分析老年人照片
- **WHEN** 调用vision.analyze_image并提供老年人照片
- **THEN** 系统返回人物状态、环境安全等分析结果

#### Scenario: 分析小朋友照片
- **WHEN** 调用vision.analyze_image并提供小朋友照片
- **THEN** 系统返回孩子情绪、安全性等分析结果

### Requirement: 系统必须支持危险场景检测
系统 需要检测图像中的危险场景，如跌倒、火灾、危险物品等，返回风险等级。

#### Scenario: 检测到跌倒
- **WHEN** 调用vision.detect_danger并提供跌倒照片
- **THEN** 系统返回风险等级为critical

#### Scenario: 正常场景
- **WHEN** 调用vision.detect_danger并提供正常活动照片
- **THEN** 系统返回风险等级为normal

### Requirement: 系统必须支持环境评估
系统 需要评估图像中的环境状况，包括地面湿滑、障碍物、光线等。

#### Scenario: 评估环境安全性
- **WHEN** 调用vision.assess_environment并提供室内照片
- **THEN** 系统返回环境安全性评估报告
