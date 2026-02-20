# Design Document: Feishu Notification System

## Overview

飞书通知系统负责将内容摘要处理的结果进行统计、格式化，并通过飞书机器人 API 推送到指定的飞书群聊。该系统作为内容处理流程的最后一环，为用户提供清晰、结构化的每日 AI 资讯简报。

系统的核心功能包括：
- 解析和统计 `summarize_all` 返回的处理结果
- 按照指定格式构建消息内容
- 通过飞书机器人 API 发送消息到群聊
- 处理各种错误情况并提供详细的日志记录

## Architecture

系统采用模块化设计，主要包含以下几个组件：

```
┌─────────────────────────────────────────────────────────┐
│                   Main Application                       │
│                  (summarize workflow)                    │
└────────────────────┬────────────────────────────────────┘
                     │ summary_result (Dict)
                     ▼
┌─────────────────────────────────────────────────────────┐
│              Notification System                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │         Statistics Calculator                    │   │
│  │  - 计算总数、成功数、失败数                        │   │
│  │  - 计算总执行时间                                  │   │
│  │  - 计算总 Token 消耗                               │   │
│  └─────────────────┬───────────────────────────────┘   │
│                    │ statistics (Dict)                  │
│                    ▼                                     │
│  ┌─────────────────────────────────────────────────┐   │
│  │         Message Builder                          │   │
│  │  - 构建执行结果总结部分                            │   │
│  │  - 构建文章清单部分                                │   │
│  │  - 格式化单个文章条目                              │   │
│  └─────────────────┬───────────────────────────────┘   │
│                    │ formatted_message (str)            │
│                    ▼                                     │
│  ┌─────────────────────────────────────────────────┐   │
│  │         Feishu Client                            │   │
│  │  - 读取配置（App ID / App Secret / Chat ID）    │   │
│  │  - 调用飞书 API 发送消息                          │   │
│  │  - 处理 API 响应和错误                            │   │
│  └─────────────────┬───────────────────────────────┘   │
└────────────────────┼────────────────────────────────────┘
                     │ success / error
                     ▼
┌─────────────────────────────────────────────────────────┐
│                   Feishu API                             │
│              (飞书群聊机器人接口)                          │
└─────────────────────────────────────────────────────────┘
```

### 数据流

1. **输入**: `summarize_all` 函数返回的 JSON 结构，包含 collection_date、target_date 和 results 数组
2. **统计计算**: 遍历 results 提取统计信息（总数、成功/失败数、时间、Token）
3. **消息构建**: 将统计信息和文章列表格式化为 Markdown 格式的消息
4. **消息发送**: 通过飞书 API 发送格式化的消息
5. **输出**: 返回发送状态（成功/失败）和相关信息

## Components and Interfaces

### 1. Statistics Calculator

**职责**: 从 summary_result 中提取和计算统计信息

**接口**:
```python
def calculate_statistics(summary_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    计算处理结果的统计信息
    
    Args:
        summary_result: summarize_all 返回的结果字典
        
    Returns:
        包含以下字段的字典:
        - total_count: int - 总文章/视频数
        - success_count: int - 成功处理数
        - failure_count: int - 失败处理数
        - total_time_minutes: int - 总执行时间（分钟）
        - total_time_seconds: int - 总执行时间（秒，不含分钟部分）
        - total_tokens: int - 总消耗 Token 数
    """
```

**实现逻辑**:
- 遍历 `results` 数组中的所有 source
- 对于每个 source，遍历其 `items` 数组
- 累加 total_count
- 根据 `success` 字段累加 success_count 或 failure_count
- 解析 `processing_time` 字符串（格式如 "2.3s"），累加总时间
- 累加 `tokens_consumed` 字段
- 将总时间转换为分钟和秒

### 2. Message Builder

**职责**: 构建符合指定格式的飞书消息内容

**接口**:
```python
def build_message(
    summary_result: Dict[str, Any],
    statistics: Dict[str, Any]
) -> str:
    """
    构建飞书消息内容
    
    Args:
        summary_result: summarize_all 返回的结果字典
        statistics: calculate_statistics 返回的统计信息
        
    Returns:
        格式化的 Markdown 消息字符串
    """
```

**消息格式**:
```markdown
## 执行结果总结

- 处理文章/视频数：{total}个，成功{success}个，失败{failure}个
- 执行时间：{minutes}分{seconds}秒
- 消耗Token：{tokens}个

## 文章清单

- {文章标题}
    * 来源：{source_title}
    * 原文链接：{url}
    * 消耗Token：{tokens_consumed}个
    * 文章简介：{brief}
    * 处理结果：{成功/失败} {失败原因（如有）}
```

**实现逻辑**:
- 使用 statistics 构建"执行结果总结"部分
- 遍历 `results` 数组构建"文章清单"部分
- 对于每个 item，提取 title、source_title、url、tokens_consumed、brief
- 根据 `success` 字段确定处理结果
- 如果失败，从 `error` 字段获取失败原因

### 3. Feishu Client

**职责**: 与飞书 API 交互，发送消息到群聊

**接口**:
```python
class FeishuClient:
    """飞书机器人客户端"""
    
    def __init__(
        self,
        app_id: str,
        app_secret: str,
        chat_receive_id: str,
        chat_receive_id_type: str = "chat_id",
        timeout: float = 30.0
    ):
        """
        初始化飞书客户端
        
        Args:
            app_id: 飞书机器人应用 App ID
            app_secret: 飞书机器人应用 App Secret
            chat_receive_id: 目标群聊接收 ID
            chat_receive_id_type: 接收 ID 类型，默认 "chat_id"
            timeout: API 请求超时时间（秒）
        """
    
    def send_message(self, content: str) -> Dict[str, Any]:
        """
        发送消息到飞书群聊
        
        Args:
            content: 消息内容（支持 Markdown 格式）
            
        Returns:
            包含以下字段的字典:
            - success: bool - 是否发送成功
            - message: str - 成功或错误信息
            - response: Optional[Dict] - API 响应内容
        """
```

**飞书 API 集成**:
- 使用应用凭证获取 `tenant_access_token`
- 使用 `im/v1/messages` 接口发送消息到群聊
- `receive_id_type` 默认使用 `chat_id`
- 消息格式使用 `post` 或 `text` 类型
- 支持 Markdown 格式的富文本消息
- 处理 API 返回的错误码和错误信息

**鉴权请求格式**:
```python
{
    "app_id": "<FEISHU_APP_ID>",
    "app_secret": "<FEISHU_APP_SECRET>"
}
```

**发送消息请求格式**:
```python
{
    "receive_id": "<FEISHU_CHAT_RECEIVE_ID>",
    "msg_type": "text",
    "content": "{\"text\":\"<消息内容>\"}"
}
```

发送 URL 示例：
`https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id`

### 4. Configuration Manager

**职责**: 管理飞书通知系统的配置

**配置项**:
- `FEISHU_APP_ID`: 飞书机器人应用 App ID（必需）
- `FEISHU_APP_SECRET`: 飞书机器人应用 App Secret（必需）
- `FEISHU_CHAT_RECEIVE_ID`: 目标群聊接收 ID（必需）
- `FEISHU_CHAT_RECEIVE_ID_TYPE`: 接收 ID 类型（可选，默认 `chat_id`）

**接口**:
```python
def load_feishu_config(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    加载飞书通知配置
    
    Args:
        config: 可选的配置字典，用于覆盖环境变量
        
    Returns:
        包含所有配置项的字典
        
    Raises:
        ConfigurationError: 当必需的配置缺失时
    """
```

### 5. Main Notification Function

**职责**: 协调所有组件，提供统一的通知接口

**接口**:
```python
def notify_feishu(
    summary_result: Dict[str, Any],
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    发送摘要结果到飞书群聊
    
    Args:
        summary_result: summarize_all 返回的结果字典
        config: 可选的配置字典
        
    Returns:
        包含以下字段的字典:
        - success: bool - 是否发送成功
        - message: str - 成功或错误信息
        - statistics: Dict - 统计信息
    """
```

**实现流程**:
1. 加载配置
2. 计算统计信息
3. 构建消息内容
4. 创建 FeishuClient 实例
5. 调用鉴权接口获取 token
6. 调用消息接口发送消息
7. 记录日志并返回结果

### 6. Example Main Entry Program

**职责**: 提供可直接运行的 notify-feishu 主入口程序，用于本地演示和联调。

**文件路径**:
- `src/samples/notify/notify.py`

**接口**:
```python
def main() -> None:
    """
    示例主入口：
    1. 构造 mock 的 Summary_Result
    2. 调用 notify_feishu
    3. 打印发送结果
    """
```

**实现要点**:
- 在示例程序内构造符合 `Summary Result Structure` 的 mock 数据
- 调用 `notify_feishu(summary_result, config=None)`
- 支持 mock 发送模式（例如通过参数或 patch requests），用于无真实飞书网络时验证发送流程
- 输出 `success`、`message`、`statistics` 字段，便于快速确认行为

## Data Models

### Summary Result Structure

输入数据结构（来自 `summarize_all`）:

```python
{
    "collection_date": str,  # 收集日期，格式 "YYYY-MM-DD"
    "target_date": str,      # 目标日期，格式 "YYYY-MM-DD"
    "results": [
        {
            "source_type": str,      # 来源类型，如 "YouTube Channels", "Blogs"
            "source_title": str,     # 来源标题，如频道名或博客名
            "success": bool,         # 该来源是否成功收集
            "items": [
                {
                    "title": str,              # 文章/视频标题
                    "url": str,                # 原文链接
                    "published": str,          # 发布时间，ISO 8601 格式
                    "processing_time": str,    # 处理时间，如 "2.3s"
                    "model_used": str,         # 使用的模型名称
                    "tokens_consumed": int,    # 消耗的 Token 数
                    "brief": str,              # 简介（100字以内）
                    "summary": str,            # 详细摘要（1000字以内）
                    "success": bool,           # 是否处理成功
                    "error": Optional[str]     # 错误信息（如失败）
                }
            ]
        }
    ]
}
```

### Statistics Structure

统计信息数据结构:

```python
{
    "total_count": int,           # 总文章/视频数
    "success_count": int,         # 成功处理数
    "failure_count": int,         # 失败处理数
    "total_time_minutes": int,    # 总执行时间（分钟部分）
    "total_time_seconds": int,    # 总执行时间（秒部分，0-59）
    "total_tokens": int           # 总消耗 Token 数
}
```

### Feishu API Response

飞书 API 响应结构:

```python
{
    "code": int,        # 错误码，0 表示成功
    "msg": str,         # 错误信息
    "data": Dict        # 响应数据
}
```

## Error Handling

### 错误类型

1. **配置错误** (`ConfigurationError`)
   - 缺少必需的配置项（如 FEISHU_APP_ID / FEISHU_APP_SECRET / FEISHU_CHAT_RECEIVE_ID）
   - 配置格式不正确

2. **数据解析错误** (`DataParseError`)
   - summary_result 格式不正确
   - 缺少必需的字段
   - 字段类型不匹配

3. **网络错误** (`NetworkError`)
   - 连接超时
   - 网络不可达
   - DNS 解析失败

4. **API 错误** (`FeishuAPIError`)
   - 飞书 API 返回错误码
   - 认证失败
   - 权限不足

### 错误处理策略

1. **配置错误**: 在初始化时立即抛出异常，阻止程序继续执行
2. **数据解析错误**: 记录详细错误日志，返回失败状态，但不中断主流程
3. **网络错误**: 记录错误日志，返回失败状态，可选择重试机制
4. **API 错误**: 记录 API 响应详情，返回失败状态

### 日志记录

使用 Python 标准 logging 模块，日志级别：
- **INFO**: 正常操作（开始发送、发送成功）
- **WARNING**: 可恢复的问题（部分数据缺失、使用默认值）
- **ERROR**: 错误情况（发送失败、API 错误）
- **DEBUG**: 详细调试信息（请求内容、响应详情）

### 容错机制

1. **缺失字段处理**: 使用默认值或空字符串，不中断处理
2. **格式异常处理**: 尝试解析，失败时使用原始值
3. **部分失败处理**: 即使部分文章处理失败，仍然发送通知
4. **发送失败处理**: 记录详细错误信息，返回失败状态，不影响主程序



## Correctness Properties

属性（Property）是关于系统行为的特征或规则，应该在所有有效执行中保持为真。属性是人类可读规格和机器可验证正确性保证之间的桥梁。通过属性测试，我们可以验证系统在各种输入下的通用正确性，而不仅仅是特定的例子。

### Property 1: 统计总数正确性

*对于任意* Summary_Result 数据，计算的 total_count 应该等于所有 results 中所有 items 的总数量。

**Validates: Requirements 1.1**

### Property 2: 成功数量统计正确性

*对于任意* Summary_Result 数据，计算的 success_count 应该等于所有 items 中 success=true 的数量。

**Validates: Requirements 1.2**

### Property 3: 失败数量统计正确性

*对于任意* Summary_Result 数据，计算的 failure_count 应该等于所有 items 中 success=false 的数量。

**Validates: Requirements 1.3**

### Property 4: 总数等于成功加失败

*对于任意* Summary_Result 数据，total_count 应该等于 success_count + failure_count。

**Validates: Requirements 1.1, 1.2, 1.3**

### Property 5: 执行时间累加正确性

*对于任意* Summary_Result 数据，计算的总执行时间（转换为秒）应该等于所有 items 的 processing_time 字段解析后的总和（允许浮点误差）。

**Validates: Requirements 1.4**

### Property 6: Token 消耗累加正确性

*对于任意* Summary_Result 数据，计算的 total_tokens 应该等于所有 items 的 tokens_consumed 字段的总和。

**Validates: Requirements 1.5**

### Property 7: 消息包含执行结果总结

*对于任意* Summary_Result 和统计信息，构建的消息应该包含"执行结果总结"标题，并且包含处理数量、执行时间和消耗 Token 的统计数字。

**Validates: Requirements 2.1**

### Property 8: 消息包含文章清单

*对于任意* Summary_Result 数据，构建的消息应该包含"文章清单"标题。

**Validates: Requirements 2.2**

### Property 9: 消息包含所有文章的必需字段

*对于任意* Summary_Result 数据，构建的消息应该包含每个文章的标题、来源、链接、Token 消耗和简介内容。

**Validates: Requirements 2.3, 2.4, 2.5, 2.6, 2.7**

### Property 10: 消息正确显示处理状态

*对于任意* Summary_Result 数据，构建的消息中每个文章条目应该根据其 success 字段显示"成功"或"失败"状态。

**Validates: Requirements 2.8**

### Property 11: 失败文章包含错误原因

*对于任意* 包含失败文章的 Summary_Result 数据，构建的消息中失败文章的条目应该包含 error 字段的内容。

**Validates: Requirements 2.9**

### Property 12: 无效数据不抛出异常

*对于任意* 格式无效的 Summary_Result 数据（如缺少字段、类型错误），notify_feishu 函数应该返回 success=false 而不是抛出未捕获的异常。

**Validates: Requirements 5.1, 5.4**

### Property 13: 空结果集处理

*对于任意* results 数组为空的 Summary_Result 数据，系统应该正确处理并生成包含零统计的消息。

**Validates: Requirements 1.1, 1.2, 1.3, 5.4**

## Testing Strategy

### 测试方法

本项目采用双重测试策略，结合单元测试和基于属性的测试（Property-Based Testing, PBT），以确保全面的代码覆盖和正确性验证。

**单元测试**:
- 验证特定的示例和边界情况
- 测试配置加载和错误处理
- 测试飞书 API 集成（使用 mock）
- 测试日志记录功能

**属性测试**:
- 验证统计计算的通用正确性
- 验证消息格式化的完整性
- 验证错误处理的鲁棒性
- 使用随机生成的数据进行大量测试

### 属性测试配置

使用 Python 的 `hypothesis` 库进行属性测试：

```python
from hypothesis import given, strategies as st

# 每个属性测试至少运行 100 次
@given(summary_result=st.builds(generate_summary_result))
@settings(max_examples=100)
def test_property_X(...):
    # 测试实现
    pass
```

每个属性测试必须：
1. 使用注释标记对应的设计文档属性
2. 格式：`# Feature: notify-feishu, Property X: <property_text>`
3. 运行至少 100 次迭代
4. 使用 hypothesis 生成随机测试数据

### 测试数据生成策略

使用 hypothesis 的 strategies 生成测试数据：

```python
# 生成文章 item
item_strategy = st.fixed_dictionaries({
    'title': st.text(min_size=1, max_size=100),
    'url': st.from_regex(r'https?://[a-z0-9.-]+/.*', fullmatch=True),
    'published': st.datetimes().map(lambda dt: dt.isoformat()),
    'processing_time': st.floats(min_value=0.1, max_value=60.0).map(lambda t: f"{t:.1f}s"),
    'model_used': st.sampled_from(['gpt-3.5-turbo', 'gpt-4', 'gemini-pro']),
    'tokens_consumed': st.integers(min_value=0, max_value=10000),
    'brief': st.text(max_size=200),
    'summary': st.text(max_size=2000),
    'success': st.booleans(),
})

# 为失败的 item 添加 error 字段
def add_error_if_failed(item):
    if not item['success']:
        item['error'] = st.text(min_size=1, max_size=100).example()
    return item

# 生成完整的 Summary_Result
summary_result_strategy = st.fixed_dictionaries({
    'collection_date': st.dates().map(lambda d: d.isoformat()),
    'target_date': st.dates().map(lambda d: d.isoformat()),
    'results': st.lists(
        st.fixed_dictionaries({
            'source_type': st.sampled_from(['YouTube Channels', 'Blogs', 'RSS Feeds']),
            'source_title': st.text(min_size=1, max_size=50),
            'success': st.booleans(),
            'items': st.lists(item_strategy, min_size=0, max_size=10)
        }),
        min_size=0,
        max_size=5
    )
})
```

### 单元测试覆盖

**Statistics Calculator 测试**:
- 测试空结果集
- 测试单个文章
- 测试多个来源和文章
- 测试时间格式解析（"2.3s", "120.5s" 等）
- 测试缺失字段的处理

**Message Builder 测试**:
- 测试消息格式的正确性
- 测试特殊字符的转义
- 测试长文本的处理
- 测试空字段的处理

**Feishu Client 测试**:
- 使用 `unittest.mock` 或 `responses` 库 mock HTTP 请求
- 测试成功发送场景
- 测试 API 错误响应
- 测试网络超时
- 测试重试机制（如实现）

**Configuration 测试**:
- 测试从环境变量加载配置
- 测试配置字典覆盖
- 测试缺失必需配置时抛出异常
- 测试默认值的使用

**Integration 测试**:
- 测试完整的 notify_feishu 流程
- 使用 mock 飞书 API
- 验证端到端的数据流

### 测试文件组织

```
tests/
├── test_statistics.py          # 统计计算测试
├── test_message_builder.py     # 消息构建测试
├── test_feishu_client.py       # 飞书客户端测试
├── test_config.py              # 配置管理测试
├── test_notify_feishu.py       # 集成测试
└── test_properties.py          # 属性测试（PBT）
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
pytest --cov=move37.notify --cov-report=html tests/
```

### 持续集成

在 CI/CD 流程中：
1. 运行所有单元测试和属性测试
2. 确保代码覆盖率 > 80%
3. 运行 linting 和类型检查（mypy）
4. 验证所有属性测试通过（100+ 迭代）
