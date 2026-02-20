# Design Document: All-in-One Workflow System

## Overview

All-in-One Workflow 系统是一个自动化的 AI 咨询服务编排系统，整合了四个核心模块：RSS 内容收集、内容总结、飞书通知和飞书知识库文档写入。系统提供两种运行模式：定时调度模式（每日自动执行）和直接执行模式（立即执行一次）。

系统的核心职责包括：
- 按照正确的顺序编排和执行各个模块
- 管理模块之间的数据流和依赖关系
- 提供命令行接口和定时任务调度
- 记录详细的执行日志和性能指标
- 生成完整的执行报告
- 处理错误情况并提供恢复机制

## Architecture

系统采用管道式架构，各模块按照固定顺序执行，前一个模块的输出作为下一个模块的输入：

```
┌─────────────────────────────────────────────────────────┐
│                   Command Line Interface                 │
│              (argparse: --direct, --help)                │
└────────────────────┬────────────────────────────────────┘
                     │ parse arguments
                     ▼
┌─────────────────────────────────────────────────────────┐
│                   Main Controller                        │
│  ┌─────────────────────────────────────────────────┐   │
│  │         Mode Selector                            │   │
│  │  - Direct Mode: execute once                     │   │
│  │  - Scheduled Mode: run at 05:00 daily            │   │
│  └─────────────────┬───────────────────────────────┘   │
└────────────────────┼────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                   Workflow Orchestrator                  │
│  ┌─────────────────────────────────────────────────┐   │
│  │         Health Check                             │   │
│  │  - Verify module imports                         │   │
│  │  - Validate configuration                        │   │
│  │  - Test Feishu API connection                    │   │
│  └─────────────────┬───────────────────────────────┘   │
│                    │ health check passed              │
│                    ▼                                     │
│  ┌─────────────────────────────────────────────────┐   │
│  │         Pipeline Executor                        │   │
│  │  Step 1: RSS Collection                          │   │
│  │  Step 2: Content Summarization                   │   │
│  │  Step 3: Feishu Notification                     │   │
│  │  Step 4: Feishu Document Writing                 │   │
│  └─────────────────┬───────────────────────────────┘   │
│                    │ execution results                │
│                    ▼                                     │
│  ┌─────────────────────────────────────────────────┐   │
│  │         Report Generator                         │   │
│  │  - Collect execution metrics                     │   │
│  │  - Generate execution report                     │   │
│  │  - Save report to file                           │   │
│  └─────────────────┬───────────────────────────────┘   │
└────────────────────┼────────────────────────────────────┘
                     │ report
                     ▼
┌─────────────────────────────────────────────────────────┐
│                   Logging System                         │
│              (console + file with rotation)              │
└─────────────────────────────────────────────────────────┘
```

### 数据流

```
┌──────────────────┐
│  RSS Collector   │
│  collect_all()   │
└────────┬─────────┘
         │ Collection_Result
         │ {collection_date, target_date, results[]}
         ▼
┌──────────────────┐
│Content Summarizer│
│ summarize_all()  │
└────────┬─────────┘
         │ Summary_Result
         │ {collection_date, target_date, results[]}
         │ (with brief, summary, tokens_consumed)
         ▼
┌──────────────────┐     ┌──────────────────┐
│ Feishu Notifier  │     │  Feishu Writer   │
│ notify_feishu()  │     │write_to_feishu   │
└────────┬─────────┘     └────────┬─────────┘
         │                        │
         │ Notification Result    │ Write Result
         │ {success, statistics}  │ {success, doc_url}
         └────────┬───────────────┘
                  ▼
         ┌──────────────────┐
         │ Execution Report │
         └──────────────────┘
```

## Components and Interfaces

### 1. Main Controller

**职责**: 程序入口点，解析命令行参数并选择运行模式

**接口**:
```python
def main() -> int:
    """
    Main entry point for the all-in-one workflow system.
    
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
```

**实现逻辑**:
- 使用 argparse 解析命令行参数
- 支持 `--direct` 参数立即执行工作流
- 支持 `--help` 显示帮助信息
- 根据参数选择运行模式
- 设置日志系统
- 捕获 KeyboardInterrupt 优雅退出
- 返回适当的退出码

### 2. Mode Selector

**职责**: 根据命令行参数选择并启动相应的运行模式

**接口**:
```python
class ModeSelector:
    """Select and execute the appropriate running mode."""
    
    @staticmethod
    def run_direct_mode() -> int:
        """
        Execute workflow once immediately.
        
        Returns:
            Exit code (0 for success, non-zero for failure)
        """
    
    @staticmethod
    def run_scheduled_mode(schedule_time: str = "05:00") -> int:
        """
        Run workflow on schedule (daily at specified time).
        
        Args:
            schedule_time: Time to run in HH:MM format (default: "05:00")
            
        Returns:
            Exit code (0 for success, non-zero for failure)
        """
```

**实现逻辑**:
- Direct Mode: 调用 WorkflowOrchestrator 执行一次工作流
- Scheduled Mode: 使用 schedule 库设置定时任务，每日在指定时间执行
- 处理 KeyboardInterrupt 信号，优雅停止调度器
- 记录模式启动和停止日志

### 3. Workflow Orchestrator

**职责**: 编排和执行完整的工作流，管理模块之间的数据流

**接口**:
```python
class WorkflowOrchestrator:
    """Orchestrate the complete workflow execution."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize workflow orchestrator.
        
        Args:
            config: Optional configuration dictionary
        """
    
    def execute_workflow(self) -> Dict[str, Any]:
        """
        Execute the complete workflow pipeline.
        
        Returns:
            Execution report dictionary containing:
            - success: bool - Overall success status
            - start_time: str - Workflow start time (ISO 8601)
            - end_time: str - Workflow end time (ISO 8601)
            - duration_seconds: float - Total execution time
            - steps: List[Dict] - Status of each step
            - metrics: Dict - Performance metrics
            - errors: List[str] - Error messages
        """
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check before workflow execution.
        
        Returns:
            Health check result dictionary:
            - success: bool - Whether health check passed
            - checks: Dict[str, bool] - Individual check results
            - errors: List[str] - Error messages
        """
```

**实现逻辑**:
1. 执行健康检查
2. 按顺序执行四个步骤
3. 验证每个步骤的输出数据格式
4. 收集性能指标
5. 生成执行报告
6. 处理错误并决定是否继续执行

### 4. Health Checker

**职责**: 在工作流执行前验证系统状态

**接口**:
```python
class HealthChecker:
    """Perform system health checks."""
    
    @staticmethod
    def check_module_imports() -> tuple[bool, Optional[str]]:
        """
        Verify all required modules can be imported.
        
        Returns:
            (success, error_message)
        """
    
    @staticmethod
    def check_configuration() -> tuple[bool, Optional[str]]:
        """
        Verify all required configuration is present.
        
        Returns:
            (success, error_message)
        """
    
    @staticmethod
    def check_feishu_connection() -> tuple[bool, Optional[str]]:
        """
        Test Feishu API connectivity.
        
        Returns:
            (success, error_message)
        """
```

**实现逻辑**:
- 尝试导入所有必需的模块
- 验证环境变量和配置文件
- 测试飞书 API 连接（获取 tenant_access_token）
- 返回详细的检查结果

### 5. Pipeline Executor

**职责**: 按顺序执行工作流的各个步骤

**接口**:
```python
class PipelineExecutor:
    """Execute workflow pipeline steps."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize pipeline executor.
        
        Args:
            config: Optional configuration dictionary
        """
    
    def execute_step_1_collection(
        self,
        target_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute Step 1: RSS Collection.
        
        Args:
            target_date: Optional target date (YYYY-MM-DD)
            
        Returns:
            Step result dictionary:
            - success: bool
            - data: Optional[Dict] - Collection result
            - duration_seconds: float
            - error: Optional[str]
        """
    
    def execute_step_2_summarization(
        self,
        collection_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute Step 2: Content Summarization.
        
        Args:
            collection_result: Output from step 1
            
        Returns:
            Step result dictionary:
            - success: bool
            - data: Optional[Dict] - Summary result
            - duration_seconds: float
            - tokens_consumed: int
            - error: Optional[str]
        """
    
    def execute_step_3_notification(
        self,
        summary_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute Step 3: Feishu Notification.
        
        Args:
            summary_result: Output from step 2
            
        Returns:
            Step result dictionary:
            - success: bool
            - data: Optional[Dict] - Notification result
            - duration_seconds: float
            - error: Optional[str]
        """
    
    def execute_step_4_document_writing(
        self,
        summary_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute Step 4: Feishu Document Writing.
        
        Args:
            summary_result: Output from step 2
            
        Returns:
            Step result dictionary:
            - success: bool
            - data: Optional[Dict] - Write result
            - duration_seconds: float
            - error: Optional[str]
        """
```

**实现逻辑**:
- 每个步骤包装对应模块的函数调用
- 记录每个步骤的开始和结束时间
- 捕获异常并转换为结构化的错误信息
- 验证输出数据格式
- 提取性能指标（如 tokens_consumed）

### 6. Data Validator

**职责**: 验证模块之间传递的数据格式

**接口**:
```python
class DataValidator:
    """Validate data structures between pipeline steps."""
    
    @staticmethod
    def validate_collection_result(data: Any) -> tuple[bool, Optional[str]]:
        """
        Validate collection result structure.
        
        Args:
            data: Data to validate
            
        Returns:
            (is_valid, error_message)
        """
    
    @staticmethod
    def validate_summary_result(data: Any) -> tuple[bool, Optional[str]]:
        """
        Validate summary result structure.
        
        Args:
            data: Data to validate
            
        Returns:
            (is_valid, error_message)
        """
```

**实现逻辑**:
- 检查数据类型（必须是 dict）
- 验证必需字段存在（collection_date, target_date, results）
- 验证字段类型正确
- 验证 results 数组结构
- 返回详细的验证错误信息

### 7. Report Generator

**职责**: 生成详细的执行报告

**接口**:
```python
class ReportGenerator:
    """Generate execution reports."""
    
    @staticmethod
    def generate_report(
        start_time: datetime,
        end_time: datetime,
        steps: List[Dict[str, Any]],
        errors: List[str]
    ) -> Dict[str, Any]:
        """
        Generate execution report.
        
        Args:
            start_time: Workflow start time
            end_time: Workflow end time
            steps: List of step results
            errors: List of error messages
            
        Returns:
            Report dictionary
        """
    
    @staticmethod
    def save_report_to_file(
        report: Dict[str, Any],
        output_dir: str = "logs/reports"
    ) -> str:
        """
        Save report to JSON file.
        
        Args:
            report: Report dictionary
            output_dir: Directory to save report
            
        Returns:
            Path to saved report file
        """
    
    @staticmethod
    def print_report_summary(report: Dict[str, Any]) -> None:
        """
        Print report summary to console.
        
        Args:
            report: Report dictionary
        """
```

**实现逻辑**:
- 计算总执行时间
- 统计成功/失败的步骤数量
- 提取性能指标（总 tokens、处理的内容数量）
- 格式化为 JSON 结构
- 保存到文件（文件名包含时间戳）
- 打印简洁的摘要到控制台

### 8. Logging System

**职责**: 配置和管理日志记录

**接口**:
```python
class LoggingSystem:
    """Configure and manage logging."""
    
    @staticmethod
    def setup_logging(
        log_level: str = "INFO",
        log_dir: str = "logs",
        log_to_console: bool = True,
        log_to_file: bool = True
    ) -> None:
        """
        Setup logging configuration.
        
        Args:
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
            log_dir: Directory for log files
            log_to_console: Whether to log to console
            log_to_file: Whether to log to file
        """
```

**实现逻辑**:
- 使用 Python logging 模块
- 配置控制台和文件两个 handler
- 文件 handler 使用 RotatingFileHandler（最大 10MB，保留 5 个备份）
- 日志格式：`%(asctime)s - %(name)s - %(levelname)s - %(message)s`
- 为不同模块设置不同的 logger

### 9. Configuration Manager

**职责**: 管理系统配置

**接口**:
```python
class ConfigurationManager:
    """Manage system configuration."""
    
    @staticmethod
    def load_config() -> Dict[str, Any]:
        """
        Load configuration from environment variables and config file.
        
        Returns:
            Configuration dictionary
            
        Raises:
            ConfigurationError: When required configuration is missing
        """
    
    @staticmethod
    def validate_config(config: Dict[str, Any]) -> None:
        """
        Validate configuration completeness.
        
        Args:
            config: Configuration dictionary
            
        Raises:
            ConfigurationError: When configuration is invalid
        """
```

**配置项**:
- `SCHEDULE_TIME`: 定时执行时间（默认 "05:00"）
- `LOG_LEVEL`: 日志级别（默认 "INFO"）
- `LOG_DIR`: 日志目录（默认 "logs"）
- `REPORT_DIR`: 报告目录（默认 "logs/reports"）
- 其他模块的配置项（通过各模块的 config 函数加载）

### 10. Scheduler

**职责**: 管理定时任务调度

**接口**:
```python
class Scheduler:
    """Manage scheduled workflow execution."""
    
    def __init__(self, schedule_time: str = "05:00"):
        """
        Initialize scheduler.
        
        Args:
            schedule_time: Time to run in HH:MM format
        """
    
    def start(self) -> None:
        """
        Start the scheduler loop.
        
        This method blocks until interrupted.
        """
    
    def stop(self) -> None:
        """
        Stop the scheduler gracefully.
        """
```

**实现逻辑**:
- 使用 `schedule` 库设置每日任务
- 在指定时间调用 WorkflowOrchestrator.execute_workflow()
- 循环检查待执行任务（每分钟检查一次）
- 捕获 KeyboardInterrupt 优雅退出
- 记录调度器启动、执行和停止日志

## Data Models

### Execution Report Structure

```python
{
    "success": bool,                    # 整体是否成功
    "start_time": str,                  # 开始时间 (ISO 8601)
    "end_time": str,                    # 结束时间 (ISO 8601)
    "duration_seconds": float,          # 总执行时间（秒）
    "steps": [
        {
            "step_number": int,         # 步骤编号
            "step_name": str,           # 步骤名称
            "success": bool,            # 是否成功
            "duration_seconds": float,  # 执行时间
            "error": Optional[str]      # 错误信息
        }
    ],
    "metrics": {
        "total_items": int,             # 处理的内容总数
        "successful_items": int,        # 成功处理数
        "failed_items": int,            # 失败处理数
        "total_tokens": int,            # 总消耗 Token
        "notification_sent": bool,      # 通知是否发送
        "documents_created": int        # 创建的文档数
    },
    "errors": List[str]                 # 错误信息列表
}
```

### Step Result Structure

```python
{
    "success": bool,                    # 步骤是否成功
    "data": Optional[Dict[str, Any]],   # 步骤输出数据
    "duration_seconds": float,          # 执行时间
    "error": Optional[str]              # 错误信息
}
```

### Health Check Result Structure

```python
{
    "success": bool,                    # 整体健康检查是否通过
    "checks": {
        "module_imports": bool,         # 模块导入检查
        "configuration": bool,          # 配置检查
        "feishu_connection": bool       # 飞书连接检查
    },
    "errors": List[str]                 # 错误信息列表
}
```

## Error Handling

### 错误类型

1. **配置错误** (`ConfigurationError`)
   - 缺少必需的配置项
   - 配置格式不正确
   - 配置值无效

2. **模块导入错误** (`ImportError`)
   - 必需的模块无法导入
   - 依赖包缺失

3. **数据验证错误** (`DataValidationError`)
   - 模块输出数据格式不正确
   - 缺少必需字段
   - 字段类型不匹配

4. **执行错误** (`ExecutionError`)
   - 模块执行失败
   - 网络错误
   - API 调用失败

### 错误处理策略

1. **健康检查失败**: 记录详细错误信息，退出程序（退出码 1）
2. **Step 1 失败**: 记录错误，停止后续步骤，生成报告，退出（退出码 1）
3. **Step 2 失败**: 记录错误，停止后续步骤，生成报告，退出（退出码 1）
4. **Step 3 失败**: 记录错误，继续执行 Step 4，生成报告，退出（退出码 0）
5. **Step 4 失败**: 记录错误，生成报告，退出（退出码 0）
6. **定时模式下失败**: 记录错误，等待下一个执行时间，不退出程序

### 日志记录

使用 Python 标准 logging 模块，日志级别：
- **DEBUG**: 详细调试信息（数据结构、API 请求/响应）
- **INFO**: 正常操作（步骤开始/完成、执行时间）
- **WARNING**: 可恢复的问题（部分数据缺失、使用默认值）
- **ERROR**: 错误情况（步骤失败、API 错误）
- **CRITICAL**: 严重错误（健康检查失败、配置错误）

日志文件：
- 主日志文件：`logs/workflow.log`（使用轮转，最大 10MB，保留 5 个备份）
- 报告文件：`logs/reports/report_YYYYMMDD_HHMMSS.json`

### 容错机制

1. **Step 3 和 Step 4 独立**: 通知失败不影响文档写入
2. **定时模式持续运行**: 单次执行失败不影响后续调度
3. **优雅退出**: 捕获 KeyboardInterrupt，清理资源后退出
4. **详细报告**: 即使失败也生成完整的执行报告

## Correctness Properties

属性（Property）是关于系统行为的特征或规则，应该在所有有效执行中保持为真。属性是人类可读规格和机器可验证正确性保证之间的桥梁。通过属性测试，我们可以验证系统在各种输入下的通用正确性，而不仅仅是特定的例子。


### Property 1: 模块执行顺序正确性

*对于任意* 工作流执行，系统应该按照固定顺序调用四个模块：RSS_Collector → Content_Summarizer → Feishu_Notifier → Feishu_Writer，且每个模块的输入应该是前一个模块的输出。

**Validates: Requirements 1.1, 1.2**

### Property 2: 早期失败停止执行

*对于任意* 工作流执行，如果 RSS_Collector 或 Content_Summarizer 执行失败，则后续模块不应该被执行。

**Validates: Requirements 1.3, 7.1, 7.2**

### Property 3: 通知失败不影响文档写入

*对于任意* 工作流执行，如果 Feishu_Notifier 执行失败，Feishu_Writer 仍然应该被执行。

**Validates: Requirements 7.3**

### Property 4: 执行报告完整性

*对于任意* 工作流执行，生成的执行报告应该包含所有已执行模块的状态信息、执行时间、性能指标（处理的内容数量、消耗的 Token）和错误信息。

**Validates: Requirements 1.4, 7.6, 9.4, 12.1**

### Property 5: 配置参数正确传递

*对于任意* 模块调用，系统应该正确传递该模块所需的配置参数。

**Validates: Requirements 2.5**

### Property 6: 无效命令行参数错误处理

*对于任意* 无效的命令行参数，系统应该显示错误信息和使用说明，而不是抛出未捕获的异常。

**Validates: Requirements 3.4**

### Property 7: 配置加载和验证

*对于任意* 系统启动，系统应该从环境变量或配置文件加载所有必需的配置参数，支持环境变量覆盖配置文件，并验证配置的有效性。当必需配置缺失时，应该抛出清晰的错误信息。

**Validates: Requirements 5.1, 5.2, 5.3, 5.5**

### Property 8: 配置默认值

*对于任意* 系统启动，如果未指定定时任务执行时间，系统应该使用默认值 "05:00"。

**Validates: Requirements 5.4**

### Property 9: 执行日志完整性

*对于任意* 工作流执行，系统应该记录工作流的开始时间、结束时间、总耗时，以及每个模块的执行状态和耗时。

**Validates: Requirements 4.4, 6.1, 6.2, 9.1, 9.2**

### Property 10: 错误日志详细性

*对于任意* 模块执行失败，系统应该记录详细的错误信息和堆栈跟踪。

**Validates: Requirements 6.3**

### Property 11: 日志配置支持

*对于任意* 系统启动，系统应该支持配置日志级别（DEBUG、INFO、WARNING、ERROR），并将日志输出到控制台和日志文件。

**Validates: Requirements 6.4, 6.5**

### Property 12: 数据结构验证

*对于任意* 模块输出，系统应该验证数据结构包含必需的字段（collection_date、target_date、results），并验证每个 result 项包含必需的字段（source_type、source_title、success、items）。当验证失败时，应该记录详细的验证错误信息并停止后续模块执行。

**Validates: Requirements 8.1, 8.2, 8.3, 8.4**

### Property 13: 性能指标收集

*对于任意* 工作流执行，系统应该记录每个模块的执行时间、整个工作流的总执行时间、Content_Summarizer 消耗的总 Token 数量，以及处理的文章/视频总数和成功/失败数量。

**Validates: Requirements 9.1, 9.2, 9.3, 9.5**

### Property 14: 启动和退出日志

*对于任意* 系统启动和退出，系统应该显示启动信息（包括版本号和运行模式）和退出信息（包括执行摘要）。

**Validates: Requirements 10.4, 10.5**

### Property 15: 健康检查完整性

*对于任意* 系统启动，系统应该执行健康检查，验证所有必需的模块可以正确导入、所有必需的配置参数已设置、飞书 API 连接可用。当健康检查失败时，应该显示详细的错误信息并退出；当健康检查成功时，应该记录成功信息并继续执行。

**Validates: Requirements 11.1, 11.2, 11.3, 11.4, 11.5**

### Property 16: 报告持久化和格式

*对于任意* 工作流执行，系统应该将执行报告保存到 JSON 格式的日志文件，并在控制台输出执行报告摘要。

**Validates: Requirements 12.2, 12.3, 12.4**

### Property 17: 独立报告文件

*对于任意* 在 Scheduled_Mode 下的工作流执行，系统应该为每次执行生成独立的报告文件（文件名包含时间戳）。

**Validates: Requirements 12.5**

## Testing Strategy

### 测试方法

本项目采用双重测试策略，结合单元测试和基于属性的测试（Property-Based Testing, PBT），以确保全面的代码覆盖和正确性验证。

**单元测试**:
- 验证特定的示例和边界情况
- 测试命令行参数解析（--direct, --help, 无参数）
- 测试配置加载和验证
- 测试健康检查各个组件
- 测试模块集成（使用 mock）
- 测试日志记录功能
- 测试报告生成和保存

**属性测试**:
- 验证模块执行顺序的正确性
- 验证错误处理和失败传播
- 验证数据验证的完整性
- 验证报告生成的完整性
- 验证配置加载和覆盖机制
- 使用随机生成的数据进行大量测试

### 属性测试配置

使用 Python 的 `hypothesis` 库进行属性测试：

```python
from hypothesis import given, strategies as st, settings

# 每个属性测试至少运行 100 次
@given(module_results=st.lists(generate_module_result()))
@settings(max_examples=100)
def test_property_X(...):
    # 测试实现
    pass
```

每个属性测试必须：
1. 使用注释标记对应的设计文档属性
2. 格式：`# Feature: all-in-one-workflow, Property X: <property_text>`
3. 运行至少 100 次迭代
4. 使用 hypothesis 生成随机测试数据

### 测试数据生成策略

使用 hypothesis 的 strategies 生成测试数据：

```python
# 生成模块执行结果
module_result_strategy = st.fixed_dictionaries({
    'success': st.booleans(),
    'data': st.one_of(st.none(), st.dictionaries(st.text(), st.text())),
    'duration_seconds': st.floats(min_value=0.1, max_value=300.0),
    'error': st.one_of(st.none(), st.text(min_size=1, max_size=100)),
})

# 生成配置字典
config_strategy = st.fixed_dictionaries({
    'SCHEDULE_TIME': st.from_regex(r'([01][0-9]|2[0-3]):[0-5][0-9]', fullmatch=True),
    'LOG_LEVEL': st.sampled_from(['DEBUG', 'INFO', 'WARNING', 'ERROR']),
    'LOG_DIR': st.text(min_size=1, max_size=50),
    'REPORT_DIR': st.text(min_size=1, max_size=50),
})

# 生成 Collection_Result
collection_result_strategy = st.fixed_dictionaries({
    'collection_date': st.dates().map(lambda d: d.isoformat()),
    'target_date': st.dates().map(lambda d: d.isoformat()),
    'results': st.lists(
        st.fixed_dictionaries({
            'source_type': st.sampled_from(['YouTube Channels', 'Blogs']),
            'source_title': st.text(min_size=1, max_size=50),
            'success': st.booleans(),
            'items': st.lists(
                st.fixed_dictionaries({
                    'title': st.text(min_size=1, max_size=100),
                    'url': st.from_regex(r'https?://[a-z0-9.-]+/.*', fullmatch=True),
                    'published': st.datetimes().map(lambda dt: dt.isoformat()),
                }),
                min_size=0,
                max_size=5
            )
        }),
        min_size=0,
        max_size=3
    )
})
```

### 单元测试覆盖

**Main Controller 测试**:
- 测试无参数启动（应该进入 Scheduled_Mode）
- 测试 --direct 参数（应该立即执行）
- 测试 --help 参数（应该显示帮助）
- 测试无效参数（应该显示错误）
- 测试 KeyboardInterrupt 处理

**Mode Selector 测试**:
- 测试 Direct Mode 执行
- 测试 Scheduled Mode 设置
- 测试调度时间配置

**Workflow Orchestrator 测试**:
- 使用 mock 测试完整工作流执行
- 测试各个步骤的顺序
- 测试数据在步骤间的传递
- 测试错误处理和失败传播
- 测试报告生成

**Health Checker 测试**:
- 测试模块导入检查
- 测试配置验证
- 测试飞书 API 连接检查（使用 mock）
- 测试健康检查失败场景

**Pipeline Executor 测试**:
- 使用 mock 测试每个步骤的执行
- 测试步骤执行时间记录
- 测试异常捕获和转换
- 测试数据验证

**Data Validator 测试**:
- 测试 Collection_Result 验证
- 测试 Summary_Result 验证
- 测试缺失字段检测
- 测试类型错误检测
- 测试嵌套结构验证

**Report Generator 测试**:
- 测试报告生成
- 测试报告保存到文件
- 测试报告摘要打印
- 测试 JSON 格式验证
- 测试文件名时间戳

**Logging System 测试**:
- 测试日志配置
- 测试不同日志级别
- 测试控制台和文件输出
- 测试日志格式

**Configuration Manager 测试**:
- 测试从环境变量加载配置
- 测试从配置文件加载配置
- 测试环境变量覆盖配置文件
- 测试缺失必需配置时抛出异常
- 测试默认值的使用
- 测试配置验证

**Scheduler 测试**:
- 使用 mock 测试调度设置
- 测试调度时间解析
- 测试调度循环（使用 mock time）

### 测试文件组织

```
tests/
├── test_main.py                    # 主入口测试
├── test_mode_selector.py           # 模式选择器测试
├── test_workflow_orchestrator.py   # 工作流编排器测试
├── test_health_checker.py          # 健康检查测试
├── test_pipeline_executor.py       # 管道执行器测试
├── test_data_validator.py          # 数据验证器测试
├── test_report_generator.py        # 报告生成器测试
├── test_logging_system.py          # 日志系统测试
├── test_config_manager.py          # 配置管理器测试
├── test_scheduler.py               # 调度器测试
└── test_properties.py              # 属性测试（PBT）
```

### 测试运行

```bash
# 运行所有测试
pytest tests/

# 运行属性测试
pytest tests/test_properties.py

# 运行单元测试
pytest tests/ --ignore=tests/test_properties.py

# 生成覆盖率报告
pytest --cov=move37.main --cov-report=html tests/
```

### 持续集成

在 CI/CD 流程中：
1. 运行所有单元测试和属性测试
2. 确保代码覆盖率 > 80%
3. 运行 linting 和类型检查（mypy）
4. 验证所有属性测试通过（100+ 迭代）
5. 检查日志记录的正确性
6. 验证报告生成功能

### 集成测试

除了单元测试和属性测试，还应该进行端到端的集成测试：

**集成测试场景**:
1. 完整工作流执行（使用真实的模块，但 mock 外部 API）
2. 定时模式运行（使用 mock 时间）
3. 错误恢复场景（模拟各种失败情况）
4. 配置变更场景（测试不同的配置组合）
5. 日志和报告验证（验证实际生成的日志和报告）

**Mock 策略**:
- Mock 飞书 API 调用（使用 responses 库）
- Mock LLM API 调用（使用 responses 库）
- Mock RSS 和 YouTube 数据获取
- Mock 时间相关函数（使用 freezegun 库）
- Mock 文件系统操作（使用 pytest tmpdir）
