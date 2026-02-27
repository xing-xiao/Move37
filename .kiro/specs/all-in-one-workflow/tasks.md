# Implementation Plan: All-in-One Workflow System

## Overview

本实现计划将 All-in-One Workflow 系统分解为一系列增量式的编码任务。系统整合四个现有模块（RSS 收集、内容总结、飞书通知、飞书文档写入），提供命令行接口和定时调度功能。实现将采用 Python 语言，遵循模块化设计原则，确保代码可测试性和可维护性。

## Tasks

- [ ] 1. 设置项目结构和核心配置
  - 在 `src/move37/` 下创建 `main.py` 作为程序入口
  - 创建 `src/move37/workflow/` 目录存放工作流相关代码
  - 创建 `src/move37/workflow/__init__.py`
  - 创建配置管理模块 `src/move37/workflow/config.py`，实现 `ConfigurationManager` 类
  - 实现从环境变量和配置文件加载配置的功能
  - 支持环境变量覆盖配置文件
  - 定义所有必需的配置项（SCHEDULE_TIME、LOG_LEVEL、LOG_DIR、REPORT_DIR）
  - 实现配置验证功能
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [ ]* 1.1 为配置管理编写属性测试
  - **Property 7: 配置加载和验证**
  - **Validates: Requirements 5.1, 5.2, 5.3, 5.5**

- [ ]* 1.2 为配置默认值编写属性测试
  - **Property 8: 配置默认值**
  - **Validates: Requirements 5.4**

- [ ] 2. 实现日志系统
  - 创建 `src/move37/workflow/logging_system.py`
  - 实现 `LoggingSystem` 类的 `setup_logging` 方法
  - 配置控制台 handler（使用 StreamHandler）
  - 配置文件 handler（使用 RotatingFileHandler，最大 10MB，保留 5 个备份）
  - 设置日志格式：`%(asctime)s - %(name)s - %(levelname)s - %(message)s`
  - 支持配置日志级别（DEBUG、INFO、WARNING、ERROR）
  - 创建日志目录（如果不存在）
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_

- [ ]* 2.1 为日志系统编写属性测试
  - **Property 11: 日志配置支持**
  - **Validates: Requirements 6.4, 6.5**

- [ ] 3. 实现数据验证器
  - 创建 `src/move37/workflow/data_validator.py`
  - 实现 `DataValidator` 类
  - 实现 `validate_collection_result` 静态方法
    - 验证数据类型为 dict
    - 验证必需字段：collection_date、target_date、results
    - 验证 results 为 list
    - 验证每个 result 项包含：source_type、source_title、success、items
  - 实现 `validate_summary_result` 静态方法
    - 验证数据类型为 dict
    - 验证必需字段：collection_date、target_date、results
    - 验证 results 为 list
    - 验证每个 result 项包含：source_type、source_title、success、items
    - 验证每个 item 包含：title、url、published、processing_time、tokens_consumed、brief、summary、success
  - 返回 (is_valid, error_message) 元组
  - _Requirements: 8.1, 8.2, 8.3, 8.4_

- [ ]* 3.1 为数据验证器编写属性测试
  - **Property 12: 数据结构验证**
  - **Validates: Requirements 8.1, 8.2, 8.3, 8.4**

- [ ] 4. 实现健康检查器
  - 创建 `src/move37/workflow/health_checker.py`
  - 实现 `HealthChecker` 类
  - 实现 `check_module_imports` 静态方法
    - 尝试导入 move37.ingest.collection
    - 尝试导入 move37.summarize.summarizer
    - 尝试导入 move37.notify.notifier
    - 尝试导入 move37.write_docx.writer
    - 返回 (success, error_message)
  - 实现 `check_configuration` 静态方法
    - 调用各模块的配置加载函数
    - 捕获 ConfigurationError
    - 返回 (success, error_message)
  - 实现 `check_feishu_connection` 静态方法
    - 创建 FeishuAPIClient 实例
    - 尝试获取 tenant_access_token
    - 返回 (success, error_message)
  - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_

- [ ]* 4.1 为健康检查器编写属性测试
  - **Property 15: 健康检查完整性**
  - **Validates: Requirements 11.1, 11.2, 11.3, 11.4, 11.5**

- [ ] 5. 实现管道执行器
  - 创建 `src/move37/workflow/pipeline_executor.py`
  - 实现 `PipelineExecutor` 类
  - 实现 `__init__` 方法，接收可选的 config 参数
  - 实现 `execute_step_1_collection` 方法
    - 调用 `collect_all(target_date)`
    - 记录开始和结束时间
    - 计算执行时间
    - 使用 DataValidator 验证输出
    - 捕获异常并转换为结构化错误
    - 返回 step result 字典
  - 实现 `execute_step_2_summarization` 方法
    - 调用 `summarize_all(collection_result, config)`
    - 记录开始和结束时间
    - 计算执行时间
    - 提取 tokens_consumed 指标
    - 使用 DataValidator 验证输出
    - 捕获异常并转换为结构化错误
    - 返回 step result 字典
  - 实现 `execute_step_3_notification` 方法
    - 调用 `notify_feishu(summary_result, config)`
    - 记录开始和结束时间
    - 计算执行时间
    - 捕获异常并转换为结构化错误
    - 返回 step result 字典
  - 实现 `execute_step_4_document_writing` 方法
    - 调用 `write_to_feishu_docx(summary_result, config)`
    - 记录开始和结束时间
    - 计算执行时间
    - 捕获异常并转换为结构化错误
    - 返回 step result 字典
  - _Requirements: 1.1, 1.2, 2.1, 2.2, 2.3, 2.4, 2.5_

- [ ]* 5.1 为管道执行器编写属性测试
  - **Property 1: 模块执行顺序正确性**
  - **Validates: Requirements 1.1, 1.2**

- [ ]* 5.2 为管道执行器编写属性测试
  - **Property 5: 配置参数正确传递**
  - **Validates: Requirements 2.5**

- [ ] 6. 实现报告生成器
  - 创建 `src/move37/workflow/report_generator.py`
  - 实现 `ReportGenerator` 类
  - 实现 `generate_report` 静态方法
    - 接收 start_time、end_time、steps、errors 参数
    - 计算 duration_seconds
    - 统计成功/失败的步骤数量
    - 从 steps 中提取性能指标（total_items、tokens、documents_created）
    - 构建 report 字典
    - 返回 report
  - 实现 `save_report_to_file` 静态方法
    - 创建报告目录（如果不存在）
    - 生成文件名（包含时间戳）：`report_YYYYMMDD_HHMMSS.json`
    - 将 report 序列化为 JSON
    - 写入文件
    - 返回文件路径
  - 实现 `print_report_summary` 静态方法
    - 打印简洁的摘要到控制台
    - 包含：总执行时间、成功/失败步骤数、处理的内容数量、消耗的 Token
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 12.1, 12.2, 12.3, 12.4, 12.5_

- [ ]* 6.1 为报告生成器编写属性测试
  - **Property 4: 执行报告完整性**
  - **Validates: Requirements 1.4, 7.6, 9.4, 12.1**

- [ ]* 6.2 为报告生成器编写属性测试
  - **Property 13: 性能指标收集**
  - **Validates: Requirements 9.1, 9.2, 9.3, 9.5**

- [ ]* 6.3 为报告生成器编写属性测试
  - **Property 16: 报告持久化和格式**
  - **Validates: Requirements 12.2, 12.3, 12.4**

- [ ]* 6.4 为报告生成器编写属性测试
  - **Property 17: 独立报告文件**
  - **Validates: Requirements 12.5**

- [ ] 7. 实现工作流编排器
  - 创建 `src/move37/workflow/orchestrator.py`
  - 实现 `WorkflowOrchestrator` 类
  - 实现 `__init__` 方法，接收可选的 config 参数
  - 实现 `health_check` 方法
    - 调用 HealthChecker 的三个检查方法
    - 收集检查结果
    - 返回 health check result 字典
  - 实现 `execute_workflow` 方法
    - 记录工作流开始时间
    - 执行健康检查，如果失败则返回错误报告
    - 创建 PipelineExecutor 实例
    - 按顺序执行四个步骤
    - 在每个步骤后验证输出数据
    - 实现错误处理逻辑：
      - Step 1 或 Step 2 失败：停止后续步骤
      - Step 3 失败：继续执行 Step 4
      - Step 4 失败：完成工作流
    - 收集所有步骤的结果
    - 记录工作流结束时间
    - 调用 ReportGenerator 生成报告
    - 保存报告到文件
    - 打印报告摘要
    - 返回执行报告
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 7.1, 7.2, 7.3, 7.4, 7.6_

- [ ]* 7.1 为工作流编排器编写属性测试
  - **Property 2: 早期失败停止执行**
  - **Validates: Requirements 1.3, 7.1, 7.2**

- [ ]* 7.2 为工作流编排器编写属性测试
  - **Property 3: 通知失败不影响文档写入**
  - **Validates: Requirements 7.3**

- [ ]* 7.3 为工作流编排器编写属性测试
  - **Property 9: 执行日志完整性**
  - **Validates: Requirements 4.4, 6.1, 6.2, 9.1, 9.2**

- [ ]* 7.4 为工作流编排器编写属性测试
  - **Property 10: 错误日志详细性**
  - **Validates: Requirements 6.3**

- [ ] 8. 实现调度器
  - 创建 `src/move37/workflow/scheduler.py`
  - 实现 `Scheduler` 类
  - 实现 `__init__` 方法，接收 schedule_time 参数（默认 "05:00"）
  - 实现 `start` 方法
    - 使用 schedule 库设置每日任务
    - 在指定时间调用 WorkflowOrchestrator.execute_workflow()
    - 进入循环，每分钟检查待执行任务
    - 捕获 KeyboardInterrupt 优雅退出
    - 记录调度器启动、执行和停止日志
  - 实现 `stop` 方法
    - 清理调度任务
    - 记录停止日志
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 7.5_

- [ ] 9. 实现模式选择器
  - 创建 `src/move37/workflow/mode_selector.py`
  - 实现 `ModeSelector` 类
  - 实现 `run_direct_mode` 静态方法
    - 创建 WorkflowOrchestrator 实例
    - 调用 execute_workflow()
    - 根据执行结果返回退出码（0 成功，1 失败）
  - 实现 `run_scheduled_mode` 静态方法
    - 接收 schedule_time 参数（默认 "05:00"）
    - 创建 Scheduler 实例
    - 调用 start() 方法
    - 捕获 KeyboardInterrupt 优雅退出
    - 返回退出码 0
  - _Requirements: 3.1, 3.2, 4.1, 4.2, 4.3, 4.5_

- [ ] 10. 实现主入口程序
  - 创建 `src/move37/main.py`
  - 实现 `main` 函数
  - 使用 argparse 解析命令行参数
    - 添加 --direct 参数：立即执行工作流
    - 添加 --help 参数：显示帮助信息
    - 添加 --schedule-time 参数：配置定时执行时间（可选）
    - 添加 --log-level 参数：配置日志级别（可选）
  - 调用 LoggingSystem.setup_logging() 设置日志
  - 显示启动信息（版本号、运行模式）
  - 根据参数选择运行模式：
    - 无参数或只有配置参数：调用 ModeSelector.run_scheduled_mode()
    - --direct 参数：调用 ModeSelector.run_direct_mode()
  - 捕获 KeyboardInterrupt 优雅退出
  - 显示退出信息和执行摘要
  - 返回退出码
  - 添加 `if __name__ == "__main__":` 块调用 main()
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 10.1, 10.2, 10.3, 10.4, 10.5_

- [ ]* 10.1 为主入口程序编写单元测试
  - 测试无参数启动（应该进入 Scheduled_Mode）
  - 测试 --direct 参数（应该立即执行）
  - 测试 --help 参数（应该显示帮助）
  - 测试无效参数（应该显示错误）
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [ ]* 10.2 为命令行参数编写属性测试
  - **Property 6: 无效命令行参数错误处理**
  - **Validates: Requirements 3.4**

- [ ]* 10.3 为启动和退出日志编写属性测试
  - **Property 14: 启动和退出日志**
  - **Validates: Requirements 10.4, 10.5**

- [ ] 11. 创建示例程序和文档
  - 创建 `src/samples/workflow/run_workflow.py` 示例程序
  - 演示如何使用 Direct Mode 执行工作流
  - 演示如何配置日志级别
  - 创建 `src/move37/workflow/README.md` 文档
  - 说明系统架构和组件
  - 说明如何运行系统（Direct Mode 和 Scheduled Mode）
  - 说明配置项和环境变量
  - 说明日志和报告的位置
  - 提供故障排查指南

- [ ] 12. Checkpoint - 确保所有测试通过
  - 运行所有单元测试：`pytest tests/ --ignore=tests/test_properties.py`
  - 运行所有属性测试：`pytest tests/test_properties.py`
  - 确保代码覆盖率 > 80%
  - 运行 linting：`ruff check src/move37/`
  - 运行类型检查：`mypy src/move37/`
  - 如有问题，询问用户

- [ ] 13. 集成测试和端到端验证
  - 创建 `tests/integration/test_workflow_integration.py`
  - 编写端到端集成测试
    - 使用 mock 外部 API（飞书、LLM）
    - 测试完整工作流执行
    - 验证日志和报告生成
    - 测试错误恢复场景
  - 编写定时模式集成测试
    - 使用 mock 时间
    - 验证调度器行为
  - 编写配置变更测试
    - 测试不同的配置组合
    - 验证配置覆盖机制

- [ ] 14. 最终 Checkpoint - 完整验证
  - 运行所有测试（单元测试、属性测试、集成测试）
  - 验证代码覆盖率 > 80%
  - 手动测试 Direct Mode：`python src/move37/main.py --direct`
  - 手动测试 Scheduled Mode：`python src/move37/main.py`（运行几分钟后 Ctrl+C）
  - 验证日志文件生成：`logs/workflow.log`
  - 验证报告文件生成：`logs/reports/report_*.json`
  - 检查文档完整性
  - 如有问题，询问用户

## Notes

- 任务标记 `*` 的为可选任务，可以跳过以加快 MVP 开发
- 每个任务引用具体的需求编号以确保可追溯性
- Checkpoint 任务确保增量验证
- 属性测试验证通用正确性属性
- 单元测试验证特定示例和边界情况
- 集成测试验证端到端流程
- 使用 mock 避免依赖外部服务
- 所有代码应该遵循 Python 最佳实践和类型提示
