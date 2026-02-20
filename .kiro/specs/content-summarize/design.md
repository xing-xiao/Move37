# 设计文档

## 概述

内容摘要系统是一个用于处理收集到的 URL 并生成中文摘要的 Python 模块。系统采用简化的架构，直接将 URL 传递给大语言模型（LLM），由 LLM 自行访问和理解内容，然后生成包含简介和深度总结的摘要。

### 设计原则

1. **简单直接**: 不进行内容预提取，直接让 LLM 处理 URL
2. **可配置性**: 支持通过配置文件或环境变量配置 LLM 参数
3. **容错性**: 单个 URL 失败不影响其他 URL 的处理
4. **可观测性**: 记录详细的处理元数据和日志

## 架构

系统采用三层架构：

```
┌─────────────────────────────────────────┐
│         summarize_all()                 │  ← 主入口函数
│    (协调器，处理 Collection_Result)      │
└─────────────────┬───────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────┐
│      summarize_single_url()             │  ← URL 处理函数
│   (处理单个 URL，记录元数据)             │
└─────────────────┬───────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────┐
│         LLMClient                       │  ← LLM 客户端
│  (调用 LLM API，处理重试和错误)         │
└─────────────────────────────────────────┘
```

### 数据流

1. `summarize_all()` 接收 `collect_all()` 返回的 JSON 数据
2. 遍历每个来源的每个 URL 项
3. 对每个 URL 调用 `summarize_single_url()`
4. `summarize_single_url()` 调用 `LLMClient.generate_summary()`
5. 记录处理时间、模型名称、token 消耗等元数据
6. **打印日志显示本次处理的结果**
7. 将摘要结果添加到原始数据结构中
8. 返回增强后的 JSON 数据

### 主入口程序

系统提供一个独立的主入口程序用于测试和演示：

- 位置：`src/samples/summarize/summarize.py`
- 功能：
  - 包含测试用的 Collection_Result JSON 数据（模拟 `collect_all()` 返回值）
  - 支持通过命令行参数指定 LLM 提供商
  - 调用 `summarize_all()` 函数
  - 输出处理结果

## 组件和接口

### 1. LLMClient 类

负责与 LLM API 交互，生成摘要内容。支持多个 LLM 提供商。

```python
class LLMClient:
    """大语言模型客户端，负责调用 LLM API 生成摘要。
    
    支持的提供商：
    - OpenAI (gpt-3.5-turbo, gpt-4, gpt-4-turbo 等)
    - DeepSeek (deepseek-chat, deepseek-coder 等)
    - Google Gemini (gemini-pro, gemini-1.5-pro 等)
    - GLM (glm-4, glm-4-plus 等)
    """
    
    def __init__(
        self,
        provider: str,
        api_key: str,
        model: str,
        base_url: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        timeout: int = 60,
        max_retries: int = 3
    ):
        """初始化 LLM 客户端。
        
        Args:
            provider: LLM 提供商名称 ("openai", "deepseek", "gemini", "glm")
            api_key: LLM API 密钥
            model: 模型名称
            base_url: API 基础 URL（可选，用于自定义端点）
            temperature: 温度参数（0-1）
            max_tokens: 最大生成 token 数
            timeout: 请求超时时间（秒）
            max_retries: 最大重试次数
        """
        pass
    
    def generate_summary(self, url: str, prompt_template: str) -> Dict[str, Any]:
        """生成 URL 内容的摘要。
        
        Args:
            url: 要摘要的 URL
            prompt_template: 提示词模板，包含 {url} 占位符
            
        Returns:
            包含以下字段的字典：
            - brief: 简介（100字以内）
            - summary: 深度总结（1000字以内）
            - model_used: 使用的模型名称
            - tokens_consumed: 消耗的 token 数
            - success: 是否成功
            - error: 错误信息（如果失败）
        """
        pass
```

**实现细节**:
- 使用统一的接口支持多个提供商
- OpenAI: 使用 `openai` Python SDK
- DeepSeek: 使用 OpenAI 兼容接口（base_url: https://api.deepseek.com）
- Gemini: 使用 `google-generativeai` SDK
- GLM: 使用 OpenAI 兼容接口（base_url: https://open.bigmodel.cn/api/paas/v4/）
- 实现指数退避重试策略
- 解析 LLM 响应，提取简介和概要
- 从响应中获取 token 使用信息
- 处理不同提供商的响应格式差异

### 2. summarize_single_url 函数

处理单个 URL 的摘要生成，记录元数据。

```python
def summarize_single_url(
    url: str,
    title: str,
    llm_client: LLMClient,
    prompt_template: str
) -> Dict[str, Any]:
    """处理单个 URL 的摘要生成。
    
    Args:
        url: 要处理的 URL
        title: URL 的标题
        llm_client: LLM 客户端实例
        prompt_template: 提示词模板
        
    Returns:
        包含处理结果和元数据的字典：
        - brief: 简介
        - summary: 概要
        - processing_time: 处理时间（秒，格式化为字符串如 "2.3s"）
        - model_used: 使用的模型
        - tokens_consumed: 消耗的 token 数
        - success: 是否成功
        - error: 错误信息（如果失败）
    """
    pass
```

**实现细节**:
- 记录开始时间
- 调用 `llm_client.generate_summary()`
- 计算处理耗时
- 格式化处理时间为字符串（如 "2.3s"）
- **打印 INFO 级别日志，显示处理结果（URL、标题、处理时间、token 消耗、简介预览）**
- 处理异常并记录错误

### 3. summarize_all 函数

主入口函数，协调整个摘要生成流程。

```python
def summarize_all(
    collection_result: Dict[str, Any],
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """对收集结果中的所有 URL 生成摘要。
    
    Args:
        collection_result: collect_all() 返回的结果
        config: 可选的配置字典，包含：
            - provider: LLM 提供商 ("openai", "deepseek", "gemini", "glm")
            - api_key: LLM API 密钥
            - model: 模型名称
            - base_url: API 基础 URL（可选）
            - temperature: 温度参数
            - max_tokens: 最大 token 数
            - timeout: 超时时间
            - max_retries: 最大重试次数
            - prompt_template: 提示词模板
            
    Returns:
        增强后的结果，每个 item 添加了摘要相关字段
    """
    pass
```

**实现细节**:
- 从配置或环境变量加载参数
- 创建 `LLMClient` 实例
- 遍历所有来源和 URL 项
- 跳过 success=false 的来源
- 对每个 URL 调用 `summarize_single_url()`
- 将结果添加到原始数据结构
- 记录处理进度日志

### 4. 配置管理

```python
def load_config(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """加载配置，优先级：传入参数 > 环境变量 > 默认值。
    
    使用 python-dotenv 从 .env 文件加载环境变量。
    
    Args:
        config: 可选的配置字典
        
    Returns:
        完整的配置字典
    """
    pass
```

**实现细节**:
- 使用 `python-dotenv` 库的 `load_dotenv()` 函数自动加载 .env 文件
- 在模块初始化时调用 `load_dotenv()`，使 .env 文件中的变量对 `os.getenv()` 可用
- 配置优先级：传入参数 > 环境变量（包括 .env 文件）> 默认值

**默认配置**:
```python
DEFAULT_CONFIG = {
    "provider": "openai",
    "model": "gpt-3.5-turbo",
    "temperature": 0.7,
    "max_tokens": 2000,
    "timeout": 60,
    "max_retries": 3,
    "prompt_template": """你是一个AI咨询专家，对我提供的链接进行总结和分析后，使用中文给我生成这个链接的简介和深入总结，帮助我理解链接中的文章或者视频信息。具体包括：
1. 100字以内的简介，能够让我直观一眼理解文章或视频的主题内容
2. 1000字以内的文章深度介绍，如果我对这篇文章感兴趣，通过阅读这1000字以内的文字内容能够理解文章或视频的主要思想、具体的亮点。

请按照以下JSON格式返回结果：
{
  "brief": "简介内容",
  "summary": "深度总结内容"
}

链接如下：{url}"""
}

# 提供商特定配置
PROVIDER_CONFIGS = {
    "openai": {
        "base_url": "https://api.openai.com/v1"
    },
    "deepseek": {
        "base_url": "https://api.deepseek.com"
    },
    "gemini": {
        # Gemini 使用不同的 SDK，不需要 base_url
    },
    "glm": {
        "base_url": "https://open.bigmodel.cn/api/paas/v4/"
    }
}
```

**环境变量**:

系统支持从 .env 文件或系统环境变量中读取配置：

- `LLM_PROVIDER`: LLM 提供商名称（"openai", "deepseek", "gemini", "glm"）
- `LLM_API_KEY`: LLM API 密钥（必需）
- `LLM_MODEL`: 模型名称
- `LLM_BASE_URL`: API 基础 URL（可选，覆盖默认值）
- `LLM_TEMPERATURE`: 温度参数
- `LLM_MAX_TOKENS`: 最大 token 数
- `LLM_TIMEOUT`: 超时时间
- `LLM_MAX_RETRIES`: 最大重试次数

**.env 文件示例**:
```bash
# LLM 提供商配置
LLM_PROVIDER=openai
LLM_API_KEY=sk-your-api-key-here
LLM_MODEL=gpt-3.5-turbo

# 可选配置
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2000
LLM_TIMEOUT=60
LLM_MAX_RETRIES=3
```

**配置加载流程**:
1. 在模块导入时，使用 `python-dotenv` 的 `load_dotenv()` 加载 .env 文件
2. .env 文件中的变量会被加载到环境变量中
3. `load_config()` 函数按优先级合并配置：传入参数 > 环境变量 > 默认值
4. 如果 API 密钥缺失，抛出 `ConfigurationError` 异常

**推荐模型配置**:
- OpenAI: `gpt-3.5-turbo`, `gpt-4`, `gpt-4-turbo`
- DeepSeek: `deepseek-chat`, `deepseek-coder`
- Gemini: `gemini-pro`, `gemini-1.5-pro`
- GLM: `glm-4`, `glm-4-plus`

## 数据模型

### 输入数据结构

```python
CollectionResult = {
    "collection_date": str,  # ISO 8601 日期格式
    "target_date": str,      # ISO 8601 日期格式
    "results": List[{
        "source_type": str,      # "Blogs" 或 "YouTube Channels"
        "source_title": str,     # 来源标题
        "success": bool,         # 是否成功收集
        "items": List[{
            "title": str,        # 内容标题
            "url": str,          # 内容 URL
            "published": str     # ISO 8601 时间戳
        }]
    }]
}
```

### 输出数据结构

```python
SummaryResult = {
    "collection_date": str,
    "target_date": str,
    "results": List[{
        "source_type": str,
        "source_title": str,
        "success": bool,
        "items": List[{
            "title": str,
            "url": str,
            "published": str,
            # 新增字段：
            "processing_time": str,      # 如 "2.3s"
            "model_used": str,           # 如 "gpt-3.5-turbo"
            "tokens_consumed": int,      # token 数量
            "brief": str,                # 简介（100字以内）
            "summary": str,              # 概要（1000字以内）
            # 如果处理失败：
            "error": Optional[str]       # 错误信息
        }]
    }]
}
```

## 正确性属性

*属性是一个特征或行为，应该在系统的所有有效执行中保持为真——本质上是关于系统应该做什么的形式化陈述。属性作为人类可读规范和机器可验证正确性保证之间的桥梁。*

### 属性 1: 结构保持性

*对于任何* 有效的 Collection_Result，处理后返回的 Summary_Result 应该保持相同的结构层次（collection_date、target_date、results 数组、source 信息）

**验证需求: 1.1, 1.2, 4.1, 4.2**

### 属性 2: URL 完整性

*对于任何* Collection_Result 中 success=true 的来源，其所有 URL 项都应该在输出中出现（无论处理成功或失败）

**验证需求: 1.1, 1.2, 4.1**

### 属性 3: 失败来源跳过

*对于任何* Collection_Result 中 success=false 的来源，其 items 不应该被处理或添加摘要字段

**验证需求: 1.3**

### 属性 4: 空输入处理

*对于任何* 空的或不包含任何项的 Collection_Result，返回的结果应该保持原始结构且不产生错误

**验证需求: 1.4**

### 属性 5: 元数据完整性

*对于任何* 成功处理的 URL，输出应该包含所有必需的元数据字段（processing_time、model_used、tokens_consumed、brief、summary）

**验证需求: 3.1, 3.2, 3.3, 3.4, 3.5, 4.4**

### 属性 6: 简介长度约束

*对于任何* 成功生成的摘要，brief 字段的长度应该不超过 100 字符

**验证需求: 2.3**

### 属性 7: 概要长度约束

*对于任何* 成功生成的摘要，summary 字段的长度应该不超过 1000 字符

**验证需求: 2.4**

### 属性 8: 错误隔离性

*对于任何* Collection_Result，如果某个 URL 处理失败，其他 URL 的处理应该继续进行且不受影响

**验证需求: 5.3**

### 属性 9: 中文输出

*对于任何* 成功生成的摘要，brief 和 summary 字段应该包含中文字符

**验证需求: 2.5**

### 属性 10: 处理时间格式

*对于任何* 成功处理的 URL，processing_time 字段应该是格式为 "X.Xs" 的字符串，其中 X 是数字

**验证需求: 3.2**

## 错误处理

### 错误类型

1. **配置错误**
   - 缺少 API 密钥
   - 无效的配置参数
   - 处理方式：抛出 `ConfigurationError` 异常，记录错误日志

2. **LLM API 错误**
   - 网络超时
   - API 限流
   - 认证失败
   - 处理方式：重试最多 3 次（指数退避），失败后在结果中标记错误

3. **响应解析错误**
   - LLM 返回格式不符合预期
   - 缺少必需字段
   - 处理方式：记录警告，尝试提取部分内容，或标记为失败

4. **数据验证错误**
   - 输入数据结构不符合预期
   - 处理方式：记录错误，跳过无效项

### 重试策略

```python
def exponential_backoff(attempt: int, base_delay: float = 1.0) -> float:
    """计算指数退避延迟时间。
    
    Args:
        attempt: 当前重试次数（从 0 开始）
        base_delay: 基础延迟时间（秒）
        
    Returns:
        延迟时间（秒）
    """
    return base_delay * (2 ** attempt)
```

- 第 1 次重试：延迟 1 秒
- 第 2 次重试：延迟 2 秒
- 第 3 次重试：延迟 4 秒

### 日志记录

使用 Python 标准库 `logging` 模块：

- **INFO**: 处理开始、完成、进度信息
- **WARNING**: 重试、部分失败
- **ERROR**: 处理失败、API 错误

日志格式：
```
[时间] [级别] [模块] - 消息 (URL: xxx, 错误: xxx)
```

## 测试策略

### 单元测试

使用 `pytest` 框架进行单元测试：

1. **LLMClient 测试**
   - 测试成功调用 API
   - 测试重试机制
   - 测试超时处理
   - 测试响应解析
   - 使用 mock 模拟 API 调用

2. **summarize_single_url 测试**
   - 测试成功场景
   - 测试失败场景
   - 测试处理时间计算
   - 测试元数据记录

3. **summarize_all 测试**
   - 测试完整流程
   - 测试空输入
   - 测试部分失败
   - 测试配置加载

4. **配置管理测试**
   - 测试默认配置
   - 测试环境变量覆盖
   - 测试参数优先级

### 属性测试

使用 `hypothesis` 库进行基于属性的测试，每个测试运行至少 100 次迭代：

1. **属性 1-4 测试**: 生成随机的 Collection_Result，验证结构保持性、URL 完整性、失败来源跳过、空输入处理
2. **属性 5 测试**: 验证成功处理的 URL 包含所有元数据字段
3. **属性 6-7 测试**: 验证简介和概要长度约束
4. **属性 8 测试**: 验证错误隔离性
5. **属性 9 测试**: 验证中文输出
6. **属性 10 测试**: 验证处理时间格式

每个属性测试必须在测试代码中使用注释标记：
```python
# Feature: content-summarize, Property 1: 结构保持性
```

### 集成测试

1. 使用真实的 LLM API 进行端到端测试（可选，需要 API 密钥）
2. 测试与 `collect_all()` 函数的集成
3. 测试不同类型的 URL（博客、YouTube）

### 测试覆盖率

目标：代码覆盖率 > 80%

使用 `pytest-cov` 生成覆盖率报告：
```bash
pytest --cov=move37.summarize --cov-report=html
```
