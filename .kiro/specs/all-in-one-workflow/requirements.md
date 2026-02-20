# Requirements Document

## Introduction

本文档定义了 AI 咨询服务自动化工作流系统的需求。该系统整合了 RSS 收集、内容总结、飞书通知和飞书文档写入四个模块，实现每日自动获取、处理和分发 AI 相关咨询信息的完整流程。

## Glossary

- **Workflow_Orchestrator**: 工作流编排器，负责协调和执行整个数据处理流程
- **Collection_Module**: RSS 收集模块，从博客和 YouTube 频道获取内容
- **Summarization_Module**: 内容总结模块，使用 LLM 对内容进行分析和总结
- **Notification_Module**: 飞书通知模块，向飞书群发送消息
- **Document_Module**: 飞书文档模块，在飞书知识库中创建和管理文档
- **Scheduler**: 定时调度器，负责在指定时间触发工作流执行
- **Direct_Mode**: 直接执行模式，通过命令行参数立即执行工作流
- **Scheduled_Mode**: 定时执行模式，按照预设时间自动执行工作流

## Requirements

### Requirement 1: 工作流编排

**User Story:** 作为系统管理员，我希望系统能够按顺序执行所有数据处理步骤，以便实现端到端的自动化流程。

#### Acceptance Criteria

1. THE Workflow_Orchestrator SHALL execute Collection_Module, Summarization_Module, Notification_Module, and Document_Module in sequential order
2. WHEN a module execution fails, THEN THE Workflow_Orchestrator SHALL log the error and continue with remaining modules
3. WHEN all modules complete, THEN THE Workflow_Orchestrator SHALL generate an execution summary report
4. THE Workflow_Orchestrator SHALL pass output data from each module to the next module as input
5. WHEN a module returns empty results, THEN THE Workflow_Orchestrator SHALL skip dependent modules and log a warning

### Requirement 2: 命令行接口

**User Story:** 作为开发者，我希望通过命令行参数控制程序的执行模式，以便在开发和生产环境中灵活使用。

#### Acceptance Criteria

1. WHEN the program is invoked without arguments, THEN THE Workflow_Orchestrator SHALL enter Scheduled_Mode
2. WHEN the program is invoked with --direct flag, THEN THE Workflow_Orchestrator SHALL execute immediately in Direct_Mode
3. THE Workflow_Orchestrator SHALL accept optional --date parameter to specify target collection date
4. THE Workflow_Orchestrator SHALL display help information when invoked with --help flag
5. WHEN invalid arguments are provided, THEN THE Workflow_Orchestrator SHALL display error message and usage information

### Requirement 3: 定时调度

**User Story:** 作为系统管理员，我希望系统能够每日自动执行，以便无需人工干预即可持续获取最新资讯。

#### Acceptance Criteria

1. WHEN in Scheduled_Mode, THE Scheduler SHALL trigger workflow execution at 5:00 AM daily
2. THE Scheduler SHALL use system local timezone for scheduling
3. WHEN the scheduled time is reached, THE Scheduler SHALL invoke the Workflow_Orchestrator
4. THE Scheduler SHALL continue running until explicitly terminated
5. WHEN a scheduled execution is in progress, THE Scheduler SHALL skip the next scheduled execution until current execution completes

### Requirement 4: 数据收集集成

**User Story:** 作为内容管理员，我希望系统能够从配置的 RSS 源和 YouTube 频道收集内容，以便获取最新的 AI 资讯。

#### Acceptance Criteria

1. THE Workflow_Orchestrator SHALL invoke Collection_Module with target date parameter
2. WHEN Collection_Module completes, THE Workflow_Orchestrator SHALL validate the returned data structure
3. THE Workflow_Orchestrator SHALL extract collection results from Collection_Module output
4. WHEN Collection_Module returns no items, THEN THE Workflow_Orchestrator SHALL log a warning and terminate the workflow
5. THE Workflow_Orchestrator SHALL pass collection results to Summarization_Module

### Requirement 5: 内容总结集成

**User Story:** 作为内容编辑，我希望系统能够自动总结收集到的内容，以便快速了解关键信息。

#### Acceptance Criteria

1. THE Workflow_Orchestrator SHALL invoke Summarization_Module with collection results
2. THE Workflow_Orchestrator SHALL pass LLM configuration to Summarization_Module
3. WHEN Summarization_Module completes, THE Workflow_Orchestrator SHALL validate the returned data structure
4. THE Workflow_Orchestrator SHALL pass summarization results to both Notification_Module and Document_Module
5. WHEN Summarization_Module fails, THEN THE Workflow_Orchestrator SHALL log the error and skip remaining modules

### Requirement 6: 飞书通知集成

**User Story:** 作为团队成员，我希望每日收到飞书群消息通知，以便及时了解最新的 AI 资讯摘要。

#### Acceptance Criteria

1. THE Workflow_Orchestrator SHALL invoke Notification_Module with summarization results
2. THE Workflow_Orchestrator SHALL pass Feishu configuration to Notification_Module
3. WHEN Notification_Module completes, THE Workflow_Orchestrator SHALL log the notification status
4. WHEN Notification_Module fails, THEN THE Workflow_Orchestrator SHALL log the error but continue with Document_Module
5. THE Workflow_Orchestrator SHALL include notification statistics in the execution summary

### Requirement 7: 飞书文档集成

**User Story:** 作为知识管理员，我希望系统能够在飞书知识库中创建结构化文档，以便长期保存和检索资讯内容。

#### Acceptance Criteria

1. THE Workflow_Orchestrator SHALL invoke Document_Module with summarization results
2. THE Workflow_Orchestrator SHALL pass Feishu wiki configuration to Document_Module
3. WHEN Document_Module completes, THE Workflow_Orchestrator SHALL log the document URL
4. WHEN Document_Module fails, THEN THE Workflow_Orchestrator SHALL log the error in the execution summary
5. THE Workflow_Orchestrator SHALL include document creation statistics in the execution summary

### Requirement 8: 错误处理和日志

**User Story:** 作为系统管理员，我希望系统能够记录详细的执行日志和错误信息，以便排查问题和监控系统运行状态。

#### Acceptance Criteria

1. THE Workflow_Orchestrator SHALL log the start and end time of each module execution
2. WHEN an error occurs, THE Workflow_Orchestrator SHALL log the error message, module name, and stack trace
3. THE Workflow_Orchestrator SHALL write logs to both console and log file
4. THE Workflow_Orchestrator SHALL use structured logging format with timestamp, level, and message
5. WHEN workflow completes, THE Workflow_Orchestrator SHALL log an execution summary with success/failure counts

### Requirement 9: 配置管理

**User Story:** 作为系统管理员，我希望系统能够从环境变量和配置文件读取配置，以便在不同环境中灵活部署。

#### Acceptance Criteria

1. THE Workflow_Orchestrator SHALL load configuration from environment variables
2. THE Workflow_Orchestrator SHALL validate required configuration parameters before execution
3. WHEN required configuration is missing, THEN THE Workflow_Orchestrator SHALL display error message and terminate
4. THE Workflow_Orchestrator SHALL pass module-specific configuration to each module
5. THE Workflow_Orchestrator SHALL support configuration override through command-line arguments

### Requirement 10: 执行报告

**User Story:** 作为系统管理员，我希望每次执行后能够获得详细的执行报告，以便了解处理结果和系统性能。

#### Acceptance Criteria

1. WHEN workflow completes, THE Workflow_Orchestrator SHALL generate an execution report
2. THE execution report SHALL include total execution time, items processed, and success/failure counts
3. THE execution report SHALL include statistics from each module (tokens consumed, documents created, etc.)
4. THE Workflow_Orchestrator SHALL save the execution report to a log file
5. THE Workflow_Orchestrator SHALL display a summary of the execution report to console
