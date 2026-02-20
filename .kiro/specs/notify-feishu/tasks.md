# Implementation Plan: Feishu Notification System

## Overview

本实现计划将飞书通知功能分解为一系列增量式的编码任务。每个任务都建立在前一个任务的基础上，确保代码逐步集成，没有孤立或未连接的代码。实现将遵循模块化设计，包括统计计算、消息构建、飞书客户端和配置管理等核心组件。

## Tasks

- [ ] 1. 创建项目结构和核心模块
  - 在 `src/move37/` 下创建 `notify` 模块目录
  - 创建 `__init__.py`、`statistics.py`、`message_builder.py`、`feishu_client.py`、`config.py` 文件
  - 定义基本的类型注解和数据结构
  - _Requirements: 1.1, 2.1, 3.1, 4.1_

- [ ] 2. 实现统计计算模块
  - [ ] 2.1 实现 `calculate_statistics` 函数
    - 解析 Summary_Result 数据结构
    - 遍历 results 和 items 数组
    - 计算总数、成功数、失败数
    - 解析 processing_time 字符串并累加时间
    - 累加 tokens_consumed
    - 将总时间转换为分钟和秒
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 6.3, 6.5_

  - [ ]* 2.2 编写统计计算的属性测试
    - **Property 1: 统计总数正确性**
    - **Validates: Requirements 1.1**

  - [ ]* 2.3 编写统计计算的属性测试
    - **Property 2: 成功数量统计正确性**
    - **Validates: Requirements 1.2**

  - [ ]* 2.4 编写统计计算的属性测试
    - **Property 3: 失败数量统计正确性**
    - **Validates: Requirements 1.3**

  - [ ]* 2.5 编写统计计算的属性测试
    - **Property 4: 总数等于成功加失败**
    - **Validates: Requirements 1.1, 1.2, 1.3**

  - [ ]* 2.6 编写统计计算的属性测试
    - **Property 5: 执行时间累加正确性**
    - **Validates: Requirements 1.4**

  - [ ]* 2.7 编写统计计算的属性测试
    - **Property 6: Token 消耗累加正确性**
    - **Validates: Requirements 1.5**

  - [ ]* 2.8 编写统计计算的单元测试
    - 测试空结果集
    - 测试单个文章
    - 测试多个来源和文章
    - 测试时间格式解析边界情况
    - 测试缺失字段的处理
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [ ] 3. 实现消息构建模块
  - [ ] 3.1 实现 `build_message` 函数
    - 构建"执行结果总结"部分
    - 格式化统计数字（处理数量、执行时间、Token）
    - 构建"文章清单"部分
    - 遍历所有文章并格式化每个条目
    - 包含标题、来源、链接、Token、简介
    - 根据 success 字段显示处理状态
    - 对于失败的文章，包含错误原因
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9, 6.1, 6.2, 6.4, 6.6_

  - [ ]* 3.2 编写消息构建的属性测试
    - **Property 7: 消息包含执行结果总结**
    - **Validates: Requirements 2.1**

  - [ ]* 3.3 编写消息构建的属性测试
    - **Property 8: 消息包含文章清单**
    - **Validates: Requirements 2.2**

  - [ ]* 3.4 编写消息构建的属性测试
    - **Property 9: 消息包含所有文章的必需字段**
    - **Validates: Requirements 2.3, 2.4, 2.5, 2.6, 2.7**

  - [ ]* 3.5 编写消息构建的属性测试
    - **Property 10: 消息正确显示处理状态**
    - **Validates: Requirements 2.8**

  - [ ]* 3.6 编写消息构建的属性测试
    - **Property 11: 失败文章包含错误原因**
    - **Validates: Requirements 2.9**

  - [ ]* 3.7 编写消息构建的单元测试
    - 测试特殊字符处理
    - 测试长文本处理
    - 测试空字段处理
    - 测试消息格式的可读性
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9_

- [ ] 4. 检查点 - 确保核心功能测试通过
  - 确保所有测试通过，如有问题请询问用户

- [ ] 5. 实现配置管理模块
  - [ ] 5.1 实现 `load_feishu_config` 函数
    - 从环境变量读取配置（FEISHU_WEBHOOK_URL, FEISHU_BOT_TOKEN, FEISHU_TIMEOUT, FEISHU_ENABLED）
    - 支持通过配置字典覆盖环境变量
    - 验证必需配置项（FEISHU_WEBHOOK_URL）
    - 设置默认值（timeout=30.0, enabled=true）
    - 缺少必需配置时抛出 ConfigurationError
    - _Requirements: 4.1, 4.2, 4.3, 4.4_

  - [ ]* 5.2 编写配置管理的单元测试
    - 测试从环境变量加载
    - 测试配置字典覆盖
    - 测试缺失必需配置时抛出异常
    - 测试默认值
    - 测试 FEISHU_ENABLED=false 的情况
    - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [ ] 6. 实现飞书客户端模块
  - [ ] 6.1 实现 `FeishuClient` 类
    - 实现 `__init__` 方法，接收 webhook_url、bot_token、timeout 参数
    - 实现 `send_message` 方法
    - 构建飞书 API 请求（使用 text 或 post 消息类型）
    - 使用 requests 库发送 HTTP POST 请求
    - 解析 API 响应，检查错误码
    - 处理网络异常（超时、连接错误）
    - 返回包含 success、message、response 的字典
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 5.2, 5.3_

  - [ ]* 6.2 编写飞书客户端的单元测试（使用 mock）
    - 使用 unittest.mock 或 responses 库 mock HTTP 请求
    - 测试成功发送场景
    - 测试 API 返回错误码
    - 测试网络超时
    - 测试连接错误
    - 验证请求格式正确
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 5.2, 5.3_

- [ ] 7. 实现主通知函数
  - [ ] 7.1 实现 `notify_feishu` 函数
    - 加载配置（调用 load_feishu_config）
    - 检查 FEISHU_ENABLED 配置
    - 调用 calculate_statistics 计算统计信息
    - 调用 build_message 构建消息
    - 创建 FeishuClient 实例
    - 调用 send_message 发送消息
    - 处理所有异常，确保不中断主流程
    - 记录详细日志（INFO、ERROR）
    - 返回包含 success、message、statistics 的字典
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 3.1, 3.2, 3.3, 4.1, 5.1, 5.4_

  - [ ]* 7.2 编写主函数的属性测试
    - **Property 12: 无效数据不抛出异常**
    - **Validates: Requirements 5.1, 5.4**

  - [ ]* 7.3 编写主函数的属性测试
    - **Property 13: 空结果集处理**
    - **Validates: Requirements 1.1, 1.2, 1.3, 5.4**

  - [ ]* 7.4 编写主函数的集成测试
    - 使用 mock 飞书 API
    - 测试完整的端到端流程
    - 测试配置错误处理
    - 测试 FEISHU_ENABLED=false 的情况
    - 验证日志记录
    - _Requirements: 3.1, 3.2, 3.3, 4.1, 4.4, 5.1, 5.2, 5.3, 5.4_

- [ ] 8. 在 `__init__.py` 中导出公共接口
  - 导出 `notify_feishu` 函数
  - 导出 `FeishuClient` 类（可选）
  - 导出 `ConfigurationError` 异常
  - 添加模块文档字符串

- [ ] 9. 创建 hypothesis 测试数据生成策略
  - [ ] 9.1 在 `tests/` 目录下创建 `strategies.py`
    - 实现 `item_strategy` 生成文章 item
    - 实现 `source_strategy` 生成来源
    - 实现 `summary_result_strategy` 生成完整的 Summary_Result
    - 实现 `invalid_summary_result_strategy` 生成无效数据
    - 确保生成的数据符合实际数据结构
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7_

- [ ] 10. 检查点 - 确保所有测试通过
  - 运行所有单元测试和属性测试
  - 确保代码覆盖率 > 80%
  - 运行 mypy 类型检查
  - 运行 ruff 或 pylint 代码检查
  - 如有问题请询问用户

- [ ] 11. 添加使用示例和文档
  - [ ] 11.1 创建 `examples/notify_feishu_example.py`
    - 展示如何使用 notify_feishu 函数
    - 展示如何配置环境变量
    - 展示如何处理返回结果
    - 包含完整的可运行示例

  - [ ] 11.2 更新 README 或创建模块文档
    - 说明功能概述
    - 说明配置要求
    - 说明使用方法
    - 说明错误处理

- [ ] 12. 集成到主工作流
  - [ ] 12.1 在主程序中调用 notify_feishu
    - 在 summarize 流程完成后调用 notify_feishu
    - 传递 summarize_all 的返回结果
    - 处理 notify_feishu 的返回状态
    - 记录通知发送结果
    - 确保通知失败不影响主流程

  - [ ]* 12.2 编写端到端集成测试
    - 测试从 summarize 到 notify 的完整流程
    - 使用 mock 外部依赖（LLM API、飞书 API）
    - 验证数据正确传递
    - _Requirements: 1.1, 2.1, 3.1, 5.4_

## Notes

- 任务标记 `*` 的为可选任务，可以跳过以加快 MVP 开发
- 每个任务都引用了具体的需求编号，确保可追溯性
- 检查点任务确保增量验证
- 属性测试验证通用正确性属性
- 单元测试验证特定示例和边界情况
- 使用 hypothesis 库进行属性测试，每个测试至少运行 100 次迭代
- 使用 unittest.mock 或 responses 库 mock 外部 API 调用
- 确保所有代码都有适当的类型注解（支持 mypy 检查）
