# Design Document: Feishu Knowledge Base Document Writer

## Overview

飞书知识库文档写入系统负责将飞书机器人推送的内容自动写入飞书知识库，创建结构化的文档层次，并对博客文章生成翻译和公众号版本。该系统作为内容处理流程的最后一环，将处理后的内容持久化到飞书知识库中，方便团队查阅和管理。

系统的核心功能包括：
- 创建以日期为标题的主文档
- 为每个内容项创建子文档，包含完整的元信息和总结
- 对博客文章生成翻译文档和公众号文章文档
- 处理各种错误情况并提供详细的日志记录

## Architecture

系统采用模块化设计，主要包含以下几个组件：

```
┌─────────────────────────────────────────────────────────┐
│                   Main Application                       │
│                  (content processing)                    │
└────────────────────┬────────────────────────────────────┘
                     │ summary_result (Dict)
                     ▼
┌─────────────────────────────────────────────────────────┐
│         Feishu Document Writer System                    │
│  ┌─────────────────────────────────────────────────┐   │
│  │         Document Manager                         │   │
│  │  - 创建/获取主文档                                 │   │
│  │  - 管理文档层次结构                                │   │
│  └─────────────────┬───────────────────────────────┘   │
│                    │ main_doc_id                        │
│                    ▼                                     │
│  ┌─────────────────────────────────────────────────┐   │
│  │         Content Processor                        │   │
│  │  - 遍历内容项                                      │   │
│  │  - 判断内容类型（博客/视频）                        │   │
│  │  - 协调子文档创建                                  │   │
│  └─────────────────┬───────────────────────────────┘   │
│                    │ content_items                      │
│                    ▼                                     │
│  ┌─────────────────────────────────────────────────┐   │
│  │         Sub-Document Builder                     │   │
│  │  - 构建子文档内容                                  │   │
│  │  - 格式化元信息和总结                              │   │
│  │  - 创建子文档                                      │   │
│  └─────────────────┬───────────────────────────────┘   │
│                    │ sub_doc_id                         │
│                    ▼                                     │
│  ┌─────────────────────────────────────────────────┐   │
│  │         Blog Article Processor                   │   │
│  │  - 提取博客内容                                    │   │
│  │  - 生成翻译文档                                    │   │
│  │  - 生成公众号文章                                  │   │
│  └─────────────────┬───────────────────────────────┘   │
│                    │ translation_doc_id                 │
│                    │ wechat_doc_id                      │
│                    ▼                                     │
│  ┌─────────────────────────────────────────────────┐   │
│  │         Feishu API Client                        │   │
│  │  - 创建文档                                        │   │
│  │  - 写入文档内容                                    │   │
│  │  - 管理文档关系                                    │   │
│  └─────────────────┬───────────────────────────────┘   │
└────────────────────┼────────────────────────────────────┘
                     │ API calls
                     ▼
┌─────────────────────────────────────────────────────────┐
│                   Feishu API                             │
│              (飞书知识库文档接口)                          │
└─────────────────────────────────────────────────────────┘
```

### 数据流

1. **输入**: 内容处理结果（包含 target_date 和 content_items）
2. **主文档创建**: 在指定 wiki space 和父节点下创建以 target_date 为标题的主文档
3. **内容项处理**: 遍历每个内容项，创建子文档
4. **博客处理**: 对博客文章，提取内容并生成翻译和公众号文档
5. **输出**: 返回处理状态和文档链接

## Components and Interfaces

### 1. Document Manager

**职责**: 管理飞书知识库文档的创建和层次结构

**接口**:
```python
class DocumentManager:
    """飞书知识库文档管理器"""
    
    def __init__(self, feishu_client: FeishuAPIClient):
        """
        初始化文档管理器
        
        Args:
            feishu_client: 飞书 API 客户端实例
        """
    
    def create_main_document(
        self,
        title: str,
        space_id: str,
        parent_node_token: str,
    ) -> str:
        """
        创建主文档
        
        Args:
            title: 文档标题（日期格式）
            space_id: 知识库 space id
            parent_node_token: 父节点 token
            
        Returns:
            文档的 node_token
            
        Raises:
            FeishuAPIError: 当 API 调用失败时
        """
    
    def create_sub_document(
        self,
        space_id: str,
        parent_node_token: str,
        title: str,
        content: str
    ) -> str:
        """
        创建子文档
        
        Args:
            space_id: 知识库 space id
            parent_node_token: 父文档的 node_token
            title: 子文档标题
            content: 子文档内容（Markdown 格式）
            
        Returns:
            子文档的 node_token
            
        Raises:
            FeishuAPIError: 当 API 调用失败时
        """
```

**实现逻辑**:
- 主文档通过 `https://open.feishu.cn/document/server-docs/docs/wiki-v2/space-node/create` 在指定 space 和父节点下创建
- 子文档通过 `https://open.feishu.cn/document/server-docs/docs/wiki-v2/space-node/create` 在主文档节点下创建
- 子文档正文通过 `https://open.feishu.cn/document/docs/docs/document-block/create-2` 写入

### 2. Content Processor

**职责**: 处理内容项，协调子文档的创建

**接口**:
```python
class ContentProcessor:
    """内容处理器"""
    
    def __init__(
        self,
        document_manager: DocumentManager,
        blog_processor: BlogArticleProcessor
    ):
        """
        初始化内容处理器
        
        Args:
            document_manager: 文档管理器实例
            blog_processor: 博客文章处理器实例
        """
    
    def process_content_items(
        self,
        main_doc_token: str,
        content_items: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        处理所有内容项
        
        Args:
            main_doc_token: 主文档的 node_token
            content_items: 内容项列表
            
        Returns:
            包含处理结果的字典:
            - total: int - 总数
            - success: int - 成功数
            - failed: int - 失败数
            - details: List[Dict] - 每个项的处理详情
        """
```

**实现逻辑**:
- 遍历所有内容项
- 判断内容类型（通过 source_type 或 URL 模式）
- 调用 SubDocumentBuilder 创建基本子文档
- 如果是博客文章，调用 BlogArticleProcessor 生成额外文档
- 收集处理结果并返回统计信息

### 3. Sub-Document Builder

**职责**: 构建子文档的内容格式

**接口**:
```python
class SubDocumentBuilder:
    """子文档内容构建器"""
    
    @staticmethod
    def build_content(content_item: Dict[str, Any]) -> str:
        """
        构建子文档内容
        
        Args:
            content_item: 内容项字典，包含以下字段:
                - title: 文章标题
                - source_title: 来源（作者/频道）
                - url: 原文链接
                - published: 发布时间
                - tokens_consumed: 消耗 Token
                - brief: 文章简介
                - summary: 文章总结
                - success: 处理结果
                - error: 错误信息（可选）
                
        Returns:
            格式化的 Markdown 内容字符串
        """
```

**文档格式**:
```markdown
## 1 文章标题

* 来源：{source_title}
* 原文链接：{url}
* 发布时间：{published}
* 消耗Token：{tokens_consumed}个
* 文章简介：{brief}
* 处理结果：{成功/失败} {错误信息}

## 2 文章总结

{summary}

## 3 翻译文章

{translation_doc_link}

## 4 生成公众号文章

{wechat_doc_link}
```

**实现逻辑**:
- 使用模板构建 Markdown 格式的内容
- 处理缺失字段，使用默认值或空字符串
- 转义特殊字符以避免 Markdown 格式错误
- 对于 YouTube 视频，不包含第 3、4 节

### 4. Blog Article Processor

**职责**: 处理博客文章，生成翻译和公众号文档

**接口**:
```python
class BlogArticleProcessor:
    """博客文章处理器"""
    
    def __init__(
        self,
        document_manager: DocumentManager,
        content_extractor: ContentExtractor,
        translator: ArticleTranslator,
        wechat_generator: WeChatArticleGenerator
    ):
        """
        初始化博客文章处理器
        
        Args:
            document_manager: 文档管理器实例
            content_extractor: 内容提取器实例
            translator: 文章翻译器实例
            wechat_generator: 公众号文章生成器实例
        """
    
    def process_blog_article(
        self,
        parent_doc_token: str,
        article_url: str,
        article_title: str
    ) -> Dict[str, Any]:
        """
        处理博客文章，生成翻译和公众号文档
        
        Args:
            parent_doc_token: 父文档的 node_token
            article_url: 博客文章 URL
            article_title: 文章标题
            
        Returns:
            包含以下字段的字典:
            - translation_doc_token: Optional[str] - 翻译文档 token
            - wechat_doc_token: Optional[str] - 公众号文档 token
            - translation_success: bool - 翻译是否成功
            - wechat_success: bool - 公众号生成是否成功
            - errors: List[str] - 错误信息列表
        """
    
    def is_blog_article(self, content_item: Dict[str, Any]) -> bool:
        """
        判断内容项是否为博客文章
        
        Args:
            content_item: 内容项字典
            
        Returns:
            True 如果是博客文章，False 如果是 YouTube 视频
        """
```

**实现逻辑**:
- 判断内容类型（通过 source_type 或 URL 模式）
- 提取博客文章的完整内容
- 调用翻译器生成翻译内容
- 调用公众号生成器生成公众号文章
- 创建对应的子文档
- 返回文档链接和处理状态

### 5. Content Extractor

**职责**: 从博客 URL 提取文章内容

**接口**:
```python
class ContentExtractor:
    """内容提取器"""
    
    def extract_article_content(self, url: str) -> str:
        """
        从 URL 提取文章内容
        
        Args:
            url: 博客文章 URL
            
        Returns:
            提取的文章内容（纯文本或 Markdown）
            
        Raises:
            ContentExtractionError: 当提取失败时
        """
```

**实现逻辑**:
- 使用 HTTP 请求获取网页内容
- 使用 BeautifulSoup 或类似库解析 HTML
- 提取主要内容区域（去除导航、广告等）
- 转换为纯文本或保留基本 Markdown 格式
- 处理各种网页结构和编码问题

### 6. Article Translator

**职责**: 使用 LLM 翻译文章内容

**接口**:
```python
class ArticleTranslator:
    """文章翻译器"""
    
    def __init__(self, llm_client: LLMClient):
        """
        初始化翻译器
        
        Args:
            llm_client: LLM 客户端实例
        """
    
    def translate_article(self, content: str) -> str:
        """
        翻译文章内容（中英对照）
        
        Args:
            content: 原文内容
            
        Returns:
            翻译后的内容，格式为：
            原文段落
            
            中文翻译
            
            原文段落
            
            中文翻译
            ...
            
        Raises:
            TranslationError: 当翻译失败时
        """
```

**实现逻辑**:
- 将文章内容按段落分割
- 对每个段落调用 LLM 进行翻译
- 按照"原文在上、译文在下"的格式组织内容
- 处理 LLM 调用失败和重试
- 记录 Token 消耗

### 7. WeChat Article Generator

**职责**: 使用 LLM 生成公众号文章

**接口**:
```python
class WeChatArticleGenerator:
    """公众号文章生成器"""
    
    def __init__(self, llm_client: LLMClient):
        """
        初始化生成器
        
        Args:
            llm_client: LLM 客户端实例
        """
    
    def generate_wechat_article(self, content: str) -> str:
        """
        生成公众号文章
        
        Args:
            content: 原文内容
            
        Returns:
            生成的公众号文章内容
            
        Raises:
            GenerationError: 当生成失败时
        """
```

**实现逻辑**:
- 使用 LLM 对原文进行总结和改写
- 使用适合 AI 咨询类公众号的风格
- 确保文章结构清晰、易读
- 处理 LLM 调用失败和重试
- 记录 Token 消耗

### 8. Feishu API Client

**职责**: 与飞书 API 交互，管理文档操作

**接口**:
```python
class FeishuAPIClient:
    """飞书 API 客户端"""
    
    def __init__(
        self,
        app_id: str,
        app_secret: str,
        timeout: float = 30.0
    ):
        """
        初始化飞书 API 客户端
        
        Args:
            app_id: 飞书应用 ID
            app_secret: 飞书应用密钥
            timeout: API 请求超时时间（秒）
        """
    
    def get_tenant_access_token(self) -> str:
        """
        获取 tenant_access_token
        
        Returns:
            访问令牌
            
        Raises:
            FeishuAPIError: 当获取失败时
        """
    
    def create_wiki_node(
        self,
        space_id: str,
        parent_node_token: str,
        title: str,
    ) -> str:
        """
        在 wiki 中创建节点（文档）
        
        Args:
            space_id: 知识库 space id
            parent_node_token: 父节点 token
            title: 文档标题
            
        Returns:
            文档的 node_token
            
        Raises:
            FeishuAPIError: 当创建失败时
        """
    
    def write_document_content(
        self,
        document_token: str,
        content: str
    ) -> None:
        """
        写入文档内容
        
        Args:
            document_token: 文档 token
            content: 文档内容（转换为 block 后写入）
            
        Raises:
            FeishuAPIError: 当写入失败时
        """
```

**飞书 API 集成**:
- 使用应用凭证获取 tenant_access_token
- 使用 `https://open.feishu.cn/document/server-docs/docs/wiki-v2/space-node/create` 创建主文档和子文档节点
- 使用 `https://open.feishu.cn/document/docs/docs/document-block/create-2` 写入文档内容块
- 处理 API 限流和重试
- 处理 API 错误响应

### 9. Configuration Manager

**职责**: 管理 write-feishu-docx 的运行配置

**必需配置项**:
- `FEISHU_APP_ID`
- `FEISHU_APP_SECRET`
- `FEISHU_WIKI_SPACE_ID`
- `FEISHU_WIKI_PARENT_NODE_TOKEN`

### 10. Main Writer Function

**职责**: 协调所有组件，提供统一的写入接口

**接口**:
```python
def write_to_feishu_docx(
    summary_result: Dict[str, Any],
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    将内容写入飞书知识库
    
    Args:
        summary_result: 内容处理结果字典，包含:
            - target_date: str - 目标日期
            - results: List[Dict] - 内容项列表
        config: 可选的配置字典
        
    Returns:
        包含以下字段的字典:
        - success: bool - 是否成功
        - main_doc_token: Optional[str] - 主文档 token
        - main_doc_url: Optional[str] - 主文档 URL
        - processed: int - 处理的内容项数量
        - errors: List[str] - 错误信息列表
    """
```

**实现流程**:
1. 加载并校验配置（必须包含 space id 和父节点 token）
2. 初始化飞书 API 客户端
3. 在指定 wiki space/父节点下创建主文档
4. 初始化各个处理器
5. 处理所有内容项
6. 记录日志并返回结果

## Data Models

### Summary Result Structure

输入数据结构:

```python
{
    "collection_date": str,  # 收集日期，格式 "YYYY-MM-DD"
    "target_date": str,      # 目标日期，格式 "YYYY-MM-DD"
    "results": [
        {
            "source_type": str,      # 来源类型，如 "YouTube Channels", "Blogs"
            "source_title": str,     # 来源标题
            "success": bool,         # 该来源是否成功收集
            "items": [
                {
                    "title": str,              # 文章/视频标题
                    "url": str,                # 原文链接
                    "published": str,          # 发布时间
                    "processing_time": str,    # 处理时间
                    "model_used": str,         # 使用的模型
                    "tokens_consumed": int,    # 消耗的 Token
                    "brief": str,              # 简介
                    "summary": str,            # 总结
                    "success": bool,           # 是否处理成功
                    "error": Optional[str]     # 错误信息
                }
            ]
        }
    ]
}
```

### Content Item Structure

单个内容项的数据结构:

```python
{
    "title": str,              # 文章标题
    "source_title": str,       # 来源
    "source_type": str,        # 来源类型
    "url": str,                # 原文链接
    "published": str,          # 发布时间
    "tokens_consumed": int,    # 消耗 Token
    "brief": str,              # 简介
    "summary": str,            # 总结
    "success": bool,           # 处理结果
    "error": Optional[str]     # 错误信息
}
```

### Document Creation Result

文档创建结果结构:

```python
{
    "node_token": str,         # 文档 token
    "document_url": str,       # 文档 URL
    "title": str,              # 文档标题
    "created_at": str          # 创建时间
}
```

### Processing Result

处理结果结构:

```python
{
    "success": bool,                    # 总体是否成功
    "main_doc_token": Optional[str],    # 主文档 token
    "main_doc_url": Optional[str],      # 主文档 URL
    "processed": int,                   # 处理的内容项数量
    "successful": int,                  # 成功数量
    "failed": int,                      # 失败数量
    "details": List[Dict],              # 每个项的详细结果
    "errors": List[str]                 # 错误信息列表
}
```

## Error Handling

### 错误类型

1. **配置错误** (`ConfigurationError`)
   - 缺少必需的配置项（如 FEISHU_APP_ID、FEISHU_APP_SECRET、FEISHU_WIKI_SPACE_ID、FEISHU_WIKI_PARENT_NODE_TOKEN）
   - 配置格式不正确

2. **API 错误** (`FeishuAPIError`)
   - 飞书 API 返回错误码
   - 认证失败
   - 权限不足
   - API 限流

3. **内容提取错误** (`ContentExtractionError`)
   - 无法访问博客 URL
   - 网页解析失败
   - 内容格式不支持

4. **LLM 错误** (`LLMError`)
   - LLM API 调用失败
   - Token 超限
   - 响应格式错误

5. **文档操作错误** (`DocumentOperationError`)
   - 文档创建失败
   - 文档写入失败

### 错误处理策略

1. **配置错误**: 在初始化时立即抛出异常，阻止程序继续执行
2. **API 错误**: 实现重试机制（最多 3 次），记录详细错误日志
3. **内容提取错误**: 记录错误，跳过该文章，继续处理其他内容
4. **LLM 错误**: 实现重试机制，记录错误，标记文档生成失败
5. **文档操作错误**: 记录错误，返回失败状态，但不中断整体流程

### 日志记录

使用 Python 标准 logging 模块，日志级别：
- **INFO**: 正常操作（开始处理、文档创建成功）
- **WARNING**: 可恢复的问题（部分内容提取失败、使用默认值）
- **ERROR**: 错误情况（API 调用失败、文档创建失败）
- **DEBUG**: 详细调试信息（API 请求内容、响应详情）

### 容错机制

1. **部分失败处理**: 单个内容项失败不影响其他项的处理
2. **重试机制**: API 调用失败时自动重试（指数退避）
3. **降级处理**: 翻译或公众号生成失败时，仍然创建基本子文档
4. **缺失字段处理**: 使用默认值或空字符串，不中断处理

## Correctness Properties

属性（Property）是关于系统行为的特征或规则，应该在所有有效执行中保持为真。属性是人类可读规格和机器可验证正确性保证之间的桥梁。通过属性测试，我们可以验证系统在各种输入下的通用正确性，而不仅仅是特定的例子。


### Property 1: 主文档创建

*对于任意* 推送内容和目标日期，系统应该在知识库中创建一个主文档，且文档标题等于目标日期。

**Validates: Requirements 1.1, 1.2**

### Property 2: 主文档写入位置正确

*对于任意* 目标日期，系统创建的主文档必须位于配置的 `Wiki_Space_ID` 与 `Parent_Node_Token` 下。

**Validates: Requirements 1.3, 10.1, 10.3**

### Property 3: 主文档创建失败处理

*对于任意* 导致主文档创建失败的情况（如 API 错误），系统应该记录错误信息并返回失败状态，而不是抛出未捕获的异常。

**Validates: Requirements 1.4**

### Property 4: 子文档创建

*对于任意* 内容项，系统应该在主文档下创建子文档，且子文档标题等于内容项的标题。

**Validates: Requirements 2.1, 2.2**

### Property 5: 子文档标识符返回

*对于任意* 成功创建的子文档，系统应该返回一个非空的唯一标识符。

**Validates: Requirements 2.3**

### Property 6: 子文档创建容错性

*对于任意* 包含多个内容项的输入，如果其中一个子文档创建失败，系统应该继续处理其他内容项，并记录失败的项。

**Validates: Requirements 2.4, 8.4**

### Property 7: 子文档包含所有必需字段

*对于任意* 内容项，生成的子文档内容应该包含文章标题、来源信息、原文链接、发布时间、Token 消耗、文章简介和处理结果状态。

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7**

### Property 8: 失败内容项包含错误信息

*对于任意* 处理失败的内容项，生成的子文档应该包含失败原因或错误信息。

**Validates: Requirements 3.8**

### Property 9: 文章总结章节存在

*对于任意* 内容项，生成的子文档应该包含"文章总结"章节，且该章节包含内容项的 summary 字段内容。

**Validates: Requirements 4.1, 4.2**

### Property 10: 博客文章生成额外文档

*对于任意* 博客类型的内容项，系统应该创建翻译文档和公众号文档作为子文档的子文档，并在子文档中包含这些文档的链接。

**Validates: Requirements 5.1, 5.2, 5.5**

### Property 11: YouTube 视频不生成额外文档

*对于任意* YouTube 视频类型的内容项，系统不应该创建翻译文档和公众号文档。

**Validates: Requirements 5.3, 5.4**

### Property 12: 博客内容提取

*对于任意* 博客文章，当生成翻译或公众号文档时，系统应该尝试从博客 URL 提取原文内容。

**Validates: Requirements 6.1, 7.1**

### Property 13: 翻译格式正确性

*对于任意* 翻译文档，内容应该遵循"原文段落在上、中文翻译在下"的格式。

**Validates: Requirements 6.3**

### Property 14: 翻译和公众号生成失败处理

*对于任意* 翻译或公众号生成失败的情况，系统应该在对应文档中记录失败原因，而不是中断整体处理流程。

**Validates: Requirements 6.5, 7.5**

### Property 15: 处理结果摘要

*对于任意* 输入，系统处理完成后应该返回包含成功数量和失败数量的处理结果摘要。

**Validates: Requirements 8.5**

### Property 16: 错误日志记录

*对于任意* 操作失败的情况（API 调用失败、LLM 调用失败等），系统应该记录详细的错误信息到日志，包括错误代码、错误消息和重试次数（如适用）。

**Validates: Requirements 8.1, 8.2, 8.3**

### Property 17: Markdown 格式正确性

*对于任意* 生成的文档内容，应该是有效的 Markdown 格式，包括正确的标题层级、列表格式、链接格式，并正确转义特殊字符。

**Validates: Requirements 9.1, 9.2, 9.3, 9.4, 9.5**

## Testing Strategy

### 测试方法

本项目采用双重测试策略，结合单元测试和基于属性的测试（Property-Based Testing, PBT），以确保全面的代码覆盖和正确性验证。

**单元测试**:
- 验证特定的示例和边界情况
- 测试配置加载和错误处理
- 测试飞书 API 集成（使用 mock）
- 测试内容提取和格式化
- 测试 LLM 调用（使用 mock）
- 测试日志记录功能

**属性测试**:
- 验证文档创建的通用正确性
- 验证内容格式化的完整性
- 验证错误处理的鲁棒性
- 验证容错机制
- 使用随机生成的数据进行大量测试

### 属性测试配置

使用 Python 的 `hypothesis` 库进行属性测试：

```python
from hypothesis import given, strategies as st, settings

# 每个属性测试至少运行 100 次
@given(content_items=st.lists(generate_content_item()))
@settings(max_examples=100)
def test_property_X(...):
    # 测试实现
    pass
```

每个属性测试必须：
1. 使用注释标记对应的设计文档属性
2. 格式：`# Feature: write-feishu-docx, Property X: <property_text>`
3. 运行至少 100 次迭代
4. 使用 hypothesis 生成随机测试数据

### 测试数据生成策略

使用 hypothesis 的 strategies 生成测试数据：

```python
# 生成内容项
content_item_strategy = st.fixed_dictionaries({
    'title': st.text(min_size=1, max_size=100),
    'source_title': st.text(min_size=1, max_size=50),
    'source_type': st.sampled_from(['YouTube Channels', 'Blogs']),
    'url': st.from_regex(r'https?://[a-z0-9.-]+/.*', fullmatch=True),
    'published': st.datetimes().map(lambda dt: dt.isoformat()),
    'tokens_consumed': st.integers(min_value=0, max_value=10000),
    'brief': st.text(max_size=200),
    'summary': st.text(max_size=2000),
    'success': st.booleans(),
})

# 为失败的项添加 error 字段
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
            'source_type': st.sampled_from(['YouTube Channels', 'Blogs']),
            'source_title': st.text(min_size=1, max_size=50),
            'success': st.booleans(),
            'items': st.lists(content_item_strategy, min_size=0, max_size=10)
        }),
        min_size=0,
        max_size=5
    )
})
```

### 单元测试覆盖

**Document Manager 测试**:
- 测试主文档创建
- 测试主文档写入到指定父节点
- 测试子文档创建
- 测试文档层次结构
- 测试 API 错误处理

**Content Processor 测试**:
- 测试内容项遍历
- 测试内容类型判断
- 测试处理结果统计
- 测试部分失败场景

**Sub-Document Builder 测试**:
- 测试文档内容格式化
- 测试必需字段包含
- 测试特殊字符转义
- 测试缺失字段处理
- 测试 YouTube 视频格式（不含翻译和公众号章节）

**Blog Article Processor 测试**:
- 测试博客文章识别
- 测试内容提取
- 测试翻译文档创建
- 测试公众号文档创建
- 测试失败场景处理

**Content Extractor 测试**:
- 使用 `responses` 库 mock HTTP 请求
- 测试成功提取场景
- 测试网络错误
- 测试解析错误
- 测试各种网页结构

**Article Translator 测试**:
- 使用 mock LLM 客户端
- 测试段落分割
- 测试翻译格式
- 测试 LLM 调用失败
- 测试重试机制

**WeChat Article Generator 测试**:
- 使用 mock LLM 客户端
- 测试文章生成
- 测试风格要求
- 测试 LLM 调用失败
- 测试重试机制

**Feishu API Client 测试**:
- 使用 `responses` 库 mock HTTP 请求
- 测试 token 获取
- 测试 wiki 节点创建（`https://open.feishu.cn/document/server-docs/docs/wiki-v2/space-node/create`）
- 测试文档内容块写入（`https://open.feishu.cn/document/docs/docs/document-block/create-2`）
- 测试 API 错误响应
- 测试重试机制

**Configuration 测试**:
- 测试从环境变量加载配置
- 测试配置字典覆盖
- 测试缺失必需配置时抛出异常
- 测试默认值的使用

**Integration 测试**:
- 测试完整的 write_to_feishu_docx 流程
- 使用 mock 飞书 API 和 LLM
- 验证端到端的数据流
- 测试各种组合场景

### 测试文件组织

```
tests/
├── test_document_manager.py        # 文档管理器测试
├── test_content_processor.py       # 内容处理器测试
├── test_sub_document_builder.py    # 子文档构建器测试
├── test_blog_processor.py          # 博客处理器测试
├── test_content_extractor.py       # 内容提取器测试
├── test_translator.py              # 翻译器测试
├── test_wechat_generator.py        # 公众号生成器测试
├── test_feishu_client.py           # 飞书客户端测试
├── test_config.py                  # 配置管理测试
├── test_write_feishu_docx.py       # 集成测试
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
pytest --cov=move37.write_docx --cov-report=html tests/
```

### 持续集成

在 CI/CD 流程中：
1. 运行所有单元测试和属性测试
2. 确保代码覆盖率 > 80%
3. 运行 linting 和类型检查（mypy）
4. 验证所有属性测试通过（100+ 迭代）
5. 检查日志记录的正确性
