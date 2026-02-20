# Requirements Document

## Introduction

本文档定义了飞书通知功能的需求规格。该功能负责将内容摘要处理的结果进行统计和格式化，并通过飞书机器人推送到指定的飞书群聊中，为用户提供每日 AI 资讯简报。

## Glossary

- **Notification_System**: 飞书通知系统，负责格式化和发送消息到飞书群聊
- **Feishu_Bot**: 飞书机器人应用，用于向群聊发送消息的接口
- **Summary_Result**: 内容摘要模块返回的处理结果数据结构
- **Statistics_Formatter**: 统计格式化器，负责计算和格式化执行统计信息
- **Message_Builder**: 消息构建器，负责按照指定格式构建飞书消息内容
- **Token**: 大语言模型处理时消耗的计量单位

## Requirements

### Requirement 1: 统计信息收集

**User Story:** 作为系统管理员，我希望系统能够自动统计内容处理的结果，以便了解每次执行的整体情况。

#### Acceptance Criteria

1. WHEN Summary_Result 被提供给 Notification_System THEN THE Statistics_Formatter SHALL 计算处理的文章/视频总数
2. WHEN Summary_Result 被提供给 Notification_System THEN THE Statistics_Formatter SHALL 计算成功处理的数量
3. WHEN Summary_Result 被提供给 Notification_System THEN THE Statistics_Formatter SHALL 计算失败处理的数量
4. WHEN Summary_Result 被提供给 Notification_System THEN THE Statistics_Formatter SHALL 计算总执行时间（分钟和秒）
5. WHEN Summary_Result 被提供给 Notification_System THEN THE Statistics_Formatter SHALL 计算总消耗的 Token 数量

### Requirement 2: 消息格式化

**User Story:** 作为飞书群成员，我希望收到格式清晰的通知消息，以便快速了解内容摘要的结果。

#### Acceptance Criteria

1. WHEN Message_Builder 构建消息 THEN THE Message_Builder SHALL 包含"执行结果总结"部分，显示处理数量、执行时间和消耗 Token
2. WHEN Message_Builder 构建消息 THEN THE Message_Builder SHALL 包含"文章清单"部分，列出所有处理的文章/视频
3. WHEN Message_Builder 格式化单个文章条目 THEN THE Message_Builder SHALL 包含文章标题
4. WHEN Message_Builder 格式化单个文章条目 THEN THE Message_Builder SHALL 包含来源信息（作者或频道名称）
5. WHEN Message_Builder 格式化单个文章条目 THEN THE Message_Builder SHALL 包含原文链接
6. WHEN Message_Builder 格式化单个文章条目 THEN THE Message_Builder SHALL 包含消耗的 Token 数量
7. WHEN Message_Builder 格式化单个文章条目 THEN THE Message_Builder SHALL 包含文章简介（brief 字段内容）
8. WHEN Message_Builder 格式化单个文章条目 THEN THE Message_Builder SHALL 包含处理结果状态（成功/失败）
9. IF 文章处理失败 THEN THE Message_Builder SHALL 在简介中包含失败原因

### Requirement 3: 飞书消息发送

**User Story:** 作为系统管理员，我希望系统能够自动将格式化的消息发送到飞书群聊，以便团队成员及时获取信息。

#### Acceptance Criteria

1. WHEN Notification_System 发送消息 THEN THE Feishu_Bot SHALL 使用飞书机器人 API 发送消息到指定群聊
2. WHEN 飞书 API 调用成功 THEN THE Notification_System SHALL 返回成功状态
3. IF 飞书 API 调用失败 THEN THE Notification_System SHALL 返回错误信息
4. WHEN 发送消息 THEN THE Feishu_Bot SHALL 使用配置的 Webhook URL 或 Bot Token

### Requirement 4: 配置管理

**User Story:** 作为系统管理员，我希望能够配置飞书机器人的连接信息，以便灵活部署到不同环境。

#### Acceptance Criteria

1. THE Notification_System SHALL 从环境变量或配置文件读取飞书机器人配置
2. THE Notification_System SHALL 支持配置 Webhook URL 或 Bot Token
3. THE Notification_System SHALL 支持配置目标群聊 ID（如需要）
4. IF 必需的配置缺失 THEN THE Notification_System SHALL 抛出配置错误异常

### Requirement 5: 错误处理

**User Story:** 作为系统管理员，我希望系统能够妥善处理各种错误情况，以便保证系统的稳定性。

#### Acceptance Criteria

1. IF Summary_Result 数据格式无效 THEN THE Notification_System SHALL 记录错误并返回失败状态
2. IF 飞书 API 返回错误 THEN THE Notification_System SHALL 记录详细错误信息
3. IF 网络连接失败 THEN THE Notification_System SHALL 记录错误并返回失败状态
4. WHEN 发生错误 THEN THE Notification_System SHALL 不中断主程序执行流程

### Requirement 6: 数据解析

**User Story:** 作为开发者，我希望系统能够正确解析 Summary_Result 的数据结构，以便准确提取所需信息。

#### Acceptance Criteria

1. WHEN 解析 Summary_Result THEN THE Notification_System SHALL 正确提取 collection_date 字段
2. WHEN 解析 Summary_Result THEN THE Notification_System SHALL 正确提取 target_date 字段
3. WHEN 解析 Summary_Result THEN THE Notification_System SHALL 正确遍历 results 数组中的所有来源
4. WHEN 解析单个来源 THEN THE Notification_System SHALL 正确提取 source_type 和 source_title
5. WHEN 解析单个来源 THEN THE Notification_System SHALL 正确遍历 items 数组中的所有文章
6. WHEN 解析单个文章 THEN THE Notification_System SHALL 正确提取 title、url、published、processing_time、tokens_consumed、brief 和 summary 字段
7. WHEN 解析单个文章 THEN THE Notification_System SHALL 正确识别处理成功或失败状态
