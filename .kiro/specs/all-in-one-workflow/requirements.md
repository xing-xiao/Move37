# Requirements Document

## Introduction

All-in-One Workflow 是一个自动化的 AI 咨询服务系统，整合了 RSS 内容收集、内容总结、飞书通知和飞书知识库文档写入四个核心模块。系统每日自动从 RSS 源和 YouTube 频道获取最新的 AI 咨询信息，使用大模型进行内容提取和总结，然后将结果推送到飞书群聊并写入飞书知识库，同时为博客文章生成翻译和公众号版本。

该系统旨在为团队提供一个完整的 AI 资讯自动化处理流程，减少人工操作，提高信息获取和分享的效率。

## Glossary

- **Workflow_System**: All-in-One Workflow 系统，整合四个核心模块的主控程序
- **RSS_Collector**: RSS 收集模块，负责从配置的 RSS 源获取内容
- **Content_Summarizer**: 内容总结模块，使用 LLM 对内容进行总结
- **Feishu_Notifier**: 飞书通知模块，负责发送消息到飞书群聊
- **Feishu_Writer**: 飞书文档写入模块，负责将内容写入飞书知识库
- **Collection_Result**: RSS 收集模块返回的数据结构
- **Summary_Result**: 内容总结模块返回的数据结构
- **Scheduler**: 定时任务调度器，负责每日定时执行工作流
- **Direct_Mode**: 直接执行模式，通过命令行参数立即执行工作流
- **Scheduled_Mode**: 定时执行模式，按照配置的时间自动执行工作流

## Requirements

### Requirement 1: 工作流程编排

**User Story:** 作为系统管理员，我希望系统能够按照正确的顺序执行各个模块，以便完成完整的内容处理流程。

#### Acceptance Criteria

1. WHEN Workflow_System 启动时，THE Workflow_System SHALL 按照以下顺序执行模块：RSS_Collector → Content_Summarizer → Feishu_Notifier → Feishu_Writer
2. WHEN 前一个模块执行成功时，THE Workflow_System SHALL 将前一个模块的输出作为下一个模块的输入
3. WHEN 任一模块执行失败时，THE Workflow_System SHALL 记录错误信息并停止后续模块的执行
4. WHEN 所有模块执行完成时，THE Workflow_System SHALL 返回包含每个模块执行状态的完整报告

### Requirement 2: 模块集成

**User Story:** 作为开发者，我希望系统能够正确集成现有的四个模块，以便复用已有的功能实现。

#### Acceptance Criteria

1. THE Workflow_System SHALL 调用 `src/move37/ingest/collection.py` 中的 `collect_all` 函数获取 Collection_Result
2. THE Workflow_System SHALL 调用 `src/move37/summarize/summarizer.py` 中的 `summarize_all` 函数处理 Collection_Result 并获取 Summary_Result
3. THE Workflow_System SHALL 调用 `src/move37/notify/notifier.py` 中的 `notify_feishu` 函数发送 Summary_Result 到飞书群聊
4. THE Workflow_System SHALL 调用 `src/move37/write_docx/writer.py` 中的 `write_to_feishu_docx` 函数将 Summary_Result 写入飞书知识库
5. WHEN 调用模块函数时，THE Workflow_System SHALL 正确传递所需的配置参数

### Requirement 3: 命令行接口

**User Story:** 作为用户，我希望能够通过命令行参数控制程序的执行模式，以便在不同场景下使用系统。

#### Acceptance Criteria

1. WHEN 用户运行 `python src/move37/main.py` 不带任何参数时，THE Workflow_System SHALL 启动 Scheduled_Mode
2. WHEN 用户运行 `python src/move37/main.py --direct` 时，THE Workflow_System SHALL 立即执行一次完整的工作流
3. WHEN 用户运行 `python src/move37/main.py --help` 时，THE Workflow_System SHALL 显示帮助信息，包括所有可用的命令行参数
4. WHEN 用户提供无效的命令行参数时，THE Workflow_System SHALL 显示错误信息和使用说明

### Requirement 4: 定时任务调度

**User Story:** 作为系统管理员，我希望系统能够每日自动执行工作流，以便无需人工干预即可获取最新资讯。

#### Acceptance Criteria

1. WHEN Workflow_System 在 Scheduled_Mode 下运行时，THE Scheduler SHALL 每日在早上 5:00 执行一次完整的工作流
2. WHEN 到达执行时间时，THE Scheduler SHALL 自动触发工作流执行
3. WHEN 工作流执行完成时，THE Scheduler SHALL 等待下一个执行时间
4. WHEN Scheduler 运行时，THE Workflow_System SHALL 记录每次执行的开始时间和结束时间
5. WHEN 用户中断程序时（如 Ctrl+C），THE Scheduler SHALL 优雅地停止并清理资源

### Requirement 5: 配置管理

**User Story:** 作为系统管理员，我希望能够通过配置文件或环境变量管理系统参数，以便灵活调整系统行为。

#### Acceptance Criteria

1. THE Workflow_System SHALL 从环境变量或配置文件加载所有必需的配置参数
2. WHEN 必需的配置参数缺失时，THE Workflow_System SHALL 在启动时抛出清晰的错误信息
3. THE Workflow_System SHALL 支持通过环境变量覆盖配置文件中的参数
4. THE Workflow_System SHALL 支持配置定时任务的执行时间（默认为 05:00）
5. THE Workflow_System SHALL 验证所有配置参数的有效性

### Requirement 6: 日志记录

**User Story:** 作为系统管理员，我希望系统能够记录详细的运行日志，以便监控系统状态和排查问题。

#### Acceptance Criteria

1. THE Workflow_System SHALL 记录每次工作流执行的开始时间、结束时间和总耗时
2. THE Workflow_System SHALL 记录每个模块的执行状态（成功/失败）和耗时
3. WHEN 模块执行失败时，THE Workflow_System SHALL 记录详细的错误信息和堆栈跟踪
4. THE Workflow_System SHALL 支持配置日志级别（DEBUG、INFO、WARNING、ERROR）
5. THE Workflow_System SHALL 将日志输出到控制台和日志文件
6. THE Workflow_System SHALL 支持日志文件轮转，避免日志文件过大

### Requirement 7: 错误处理和恢复

**User Story:** 作为系统管理员，我希望系统能够妥善处理错误情况，以便提高系统的稳定性和可靠性。

#### Acceptance Criteria

1. WHEN RSS_Collector 执行失败时，THE Workflow_System SHALL 记录错误并停止后续模块执行
2. WHEN Content_Summarizer 执行失败时，THE Workflow_System SHALL 记录错误并停止后续模块执行
3. WHEN Feishu_Notifier 执行失败时，THE Workflow_System SHALL 记录错误但继续执行 Feishu_Writer
4. WHEN Feishu_Writer 执行失败时，THE Workflow_System SHALL 记录错误并完成工作流
5. WHEN 在 Scheduled_Mode 下工作流执行失败时，THE Scheduler SHALL 等待下一个执行时间而不是退出程序
6. THE Workflow_System SHALL 为每次执行生成执行报告，包含所有模块的状态和错误信息

### Requirement 8: 数据流验证

**User Story:** 作为开发者，我希望系统能够验证模块之间传递的数据格式，以便及早发现数据不一致问题。

#### Acceptance Criteria

1. WHEN RSS_Collector 返回 Collection_Result 时，THE Workflow_System SHALL 验证数据结构包含必需的字段（collection_date、target_date、results）
2. WHEN Content_Summarizer 返回 Summary_Result 时，THE Workflow_System SHALL 验证数据结构包含必需的字段（collection_date、target_date、results）
3. WHEN 数据验证失败时，THE Workflow_System SHALL 记录详细的验证错误信息并停止后续模块执行
4. THE Workflow_System SHALL 验证每个 result 项包含必需的字段（source_type、source_title、success、items）

### Requirement 9: 性能监控

**User Story:** 作为系统管理员，我希望系统能够记录性能指标，以便监控和优化系统性能。

#### Acceptance Criteria

1. THE Workflow_System SHALL 记录每个模块的执行时间
2. THE Workflow_System SHALL 记录整个工作流的总执行时间
3. THE Workflow_System SHALL 记录 Content_Summarizer 消耗的总 Token 数量
4. THE Workflow_System SHALL 在执行报告中包含所有性能指标
5. THE Workflow_System SHALL 记录处理的文章/视频总数和成功/失败数量

### Requirement 10: 程序入口

**User Story:** 作为开发者，我希望有一个清晰的程序入口点，以便正确启动和管理系统。

#### Acceptance Criteria

1. THE Workflow_System SHALL 在 `src/move37/main.py` 中提供主入口函数
2. THE Workflow_System SHALL 支持作为 Python 模块运行（`python -m move37.main`）
3. THE Workflow_System SHALL 支持作为脚本直接运行（`python src/move37/main.py`）
4. WHEN 程序启动时，THE Workflow_System SHALL 显示启动信息，包括版本号和运行模式
5. WHEN 程序退出时，THE Workflow_System SHALL 显示退出信息和执行摘要

### Requirement 11: 健康检查

**User Story:** 作为系统管理员，我希望系统能够在启动时进行健康检查，以便确保所有依赖和配置正确。

#### Acceptance Criteria

1. WHEN Workflow_System 启动时，THE Workflow_System SHALL 验证所有必需的模块可以正确导入
2. WHEN Workflow_System 启动时，THE Workflow_System SHALL 验证所有必需的配置参数已设置
3. WHEN Workflow_System 启动时，THE Workflow_System SHALL 验证飞书 API 连接可用
4. WHEN 健康检查失败时，THE Workflow_System SHALL 显示详细的错误信息并退出
5. WHEN 健康检查成功时，THE Workflow_System SHALL 记录成功信息并继续执行

### Requirement 12: 执行报告

**User Story:** 作为系统管理员，我希望系统能够生成详细的执行报告，以便了解每次执行的结果。

#### Acceptance Criteria

1. WHEN 工作流执行完成时，THE Workflow_System SHALL 生成包含以下信息的执行报告：执行时间、各模块状态、处理的内容数量、消耗的 Token、错误信息
2. THE Workflow_System SHALL 将执行报告保存到日志文件
3. THE Workflow_System SHALL 在控制台输出执行报告摘要
4. THE Workflow_System SHALL 支持将执行报告导出为 JSON 格式
5. WHEN 在 Scheduled_Mode 下运行时，THE Workflow_System SHALL 为每次执行生成独立的报告文件
