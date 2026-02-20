# Implementation Plan: Feishu Knowledge Base Document Writer

## Overview

本实施计划将飞书知识库文档写入系统分解为一系列可执行的编码任务。系统将自动创建结构化的飞书文档，包括主文档、子文档，以及针对博客文章的翻译和公众号版本。实施将采用增量方式，每个步骤都建立在前一步的基础上，确保功能逐步完善并可验证。

## Tasks

- [ ] 1. 设置项目结构和核心配置
  - 创建 `src/move37/write_docx/` 目录结构
  - 创建 `__init__.py` 文件
  - 定义配置管理模块，从环境变量读取飞书 API 配置（含 `FEISHU_WIKI_SPACE_ID`、`FEISHU_WIKI_PARENT_NODE_TOKEN`）
  - 添加必要的依赖到 `requirements.txt`（如 `requests`, `beautifulsoup4`）
  - _Requirements: 8.1, 10.3, 10.4_

- [ ] 2. 实现飞书 API 客户端
  - [ ] 2.1 创建 `FeishuAPIClient` 类
    - 实现 `get_tenant_access_token()` 方法获取访问令牌
    - 实现 `create_wiki_node()` 方法调用 `https://open.feishu.cn/document/server-docs/docs/wiki-v2/space-node/create` 创建节点
    - 实现 `write_document_content()` 方法调用 `https://open.feishu.cn/document/docs/docs/document-block/create-2` 写入内容块
    - 实现错误处理和重试机制
    - _Requirements: 1.1, 1.4, 2.1, 2.4, 8.2, 10.1, 10.2_
  
  - [ ]* 2.2 编写 FeishuAPIClient 的单元测试
    - 使用 `responses` 库 mock HTTP 请求
    - 测试成功场景和错误场景
    - 测试重试机制
    - _Requirements: 1.4, 8.2_

- [ ] 3. 实现文档管理器
  - [ ] 3.1 创建 `DocumentManager` 类
    - 实现 `create_main_document()` 方法
    - 实现 `create_sub_document()` 方法
    - 基于 `space_id + parent_node_token` 创建主文档和子文档
    - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.2, 2.3, 10.1, 10.3_
  
  - [ ]* 3.2 编写属性测试：主文档创建
    - **Property 1: 主文档创建**
    - **Validates: Requirements 1.1, 1.2**
  
  - [ ]* 3.3 编写属性测试：主文档写入位置正确
    - **Property 2: 主文档写入位置正确**
    - **Validates: Requirements 1.3, 10.1, 10.3**
  
  - [ ]* 3.4 编写属性测试：主文档创建失败处理
    - **Property 3: 主文档创建失败处理**
    - **Validates: Requirements 1.4**

- [ ] 4. 实现子文档内容构建器
  - [ ] 4.1 创建 `SubDocumentBuilder` 类
    - 实现 `build_content()` 静态方法
    - 实现 Markdown 格式化逻辑
    - 实现特殊字符转义
    - 处理缺失字段，使用默认值
    - 根据内容类型决定是否包含翻译和公众号章节
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 4.1, 4.2, 4.3, 9.1, 9.2, 9.3, 9.4, 9.5_
  
  - [ ]* 4.2 编写属性测试：子文档包含所有必需字段
    - **Property 7: 子文档包含所有必需字段**
    - **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7**
  
  - [ ]* 4.3 编写属性测试：失败内容项包含错误信息
    - **Property 8: 失败内容项包含错误信息**
    - **Validates: Requirements 3.8**
  
  - [ ]* 4.4 编写属性测试：文章总结章节存在
    - **Property 9: 文章总结章节存在**
    - **Validates: Requirements 4.1, 4.2**
  
  - [ ]* 4.5 编写属性测试：Markdown 格式正确性
    - **Property 17: Markdown 格式正确性**
    - **Validates: Requirements 9.1, 9.2, 9.3, 9.4, 9.5**
  
  - [ ]* 4.6 编写单元测试
    - 测试特殊字符转义
    - 测试空字段处理
    - 测试 YouTube 视频格式（不含翻译和公众号章节）
    - _Requirements: 9.5, 4.3_

- [ ] 5. 检查点 - 确保基础文档创建功能正常
  - 确保所有测试通过，如有问题请询问用户

- [ ] 6. 实现内容提取器
  - [ ] 6.1 创建 `ContentExtractor` 类
    - 实现 `extract_article_content()` 方法
    - 使用 `requests` 获取网页内容
    - 使用 `BeautifulSoup` 解析 HTML
    - 提取主要内容区域
    - 处理各种编码和网页结构
    - _Requirements: 6.1, 7.1_
  
  - [ ]* 6.2 编写单元测试
    - 使用 `responses` 库 mock HTTP 请求
    - 测试成功提取场景
    - 测试网络错误
    - 测试解析错误
    - _Requirements: 6.1_

- [ ] 7. 实现文章翻译器
  - [ ] 7.1 创建 `ArticleTranslator` 类
    - 实现 `translate_article()` 方法
    - 实现段落分割逻辑
    - 调用 LLM 进行翻译
    - 实现"原文在上、译文在下"的格式化
    - 实现错误处理和重试
    - _Requirements: 6.2, 6.3, 6.4, 6.5, 8.3_
  
  - [ ]* 7.2 编写属性测试：翻译格式正确性
    - **Property 13: 翻译格式正确性**
    - **Validates: Requirements 6.3**
  
  - [ ]* 7.3 编写单元测试
    - 使用 mock LLM 客户端
    - 测试段落分割
    - 测试翻译格式
    - 测试 LLM 调用失败
    - _Requirements: 6.2, 6.5_

- [ ] 8. 实现公众号文章生成器
  - [ ] 8.1 创建 `WeChatArticleGenerator` 类
    - 实现 `generate_wechat_article()` 方法
    - 调用 LLM 进行总结和改写
    - 使用适合 AI 咨询类公众号的提示词
    - 实现错误处理和重试
    - _Requirements: 7.2, 7.4, 7.5, 8.3_
  
  - [ ]* 8.2 编写单元测试
    - 使用 mock LLM 客户端
    - 测试文章生成
    - 测试 LLM 调用失败
    - _Requirements: 7.2, 7.5_

- [ ] 9. 实现博客文章处理器
  - [ ] 9.1 创建 `BlogArticleProcessor` 类
    - 实现 `is_blog_article()` 方法判断内容类型
    - 实现 `process_blog_article()` 方法
    - 协调内容提取、翻译和公众号生成
    - 创建翻译和公众号子文档
    - 处理各种错误情况
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 6.1, 6.4, 6.5, 7.1, 7.4, 7.5_
  
  - [ ]* 9.2 编写属性测试：博客文章生成额外文档
    - **Property 10: 博客文章生成额外文档**
    - **Validates: Requirements 5.1, 5.2, 5.5**
  
  - [ ]* 9.3 编写属性测试：YouTube 视频不生成额外文档
    - **Property 11: YouTube 视频不生成额外文档**
    - **Validates: Requirements 5.3, 5.4**
  
  - [ ]* 9.4 编写属性测试：博客内容提取
    - **Property 12: 博客内容提取**
    - **Validates: Requirements 6.1, 7.1**
  
  - [ ]* 9.5 编写属性测试：翻译和公众号生成失败处理
    - **Property 14: 翻译和公众号生成失败处理**
    - **Validates: Requirements 6.5, 7.5**

- [ ] 10. 检查点 - 确保博客处理功能正常
  - 确保所有测试通过，如有问题请询问用户

- [ ] 11. 实现内容处理器
  - [ ] 11.1 创建 `ContentProcessor` 类
    - 实现 `process_content_items()` 方法
    - 遍历所有内容项
    - 调用 SubDocumentBuilder 创建子文档
    - 对博客文章调用 BlogArticleProcessor
    - 收集处理结果和统计信息
    - 实现容错机制（单个失败不影响其他项）
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 8.4, 8.5_
  
  - [ ]* 11.2 编写属性测试：子文档创建
    - **Property 4: 子文档创建**
    - **Validates: Requirements 2.1, 2.2**
  
  - [ ]* 11.3 编写属性测试：子文档标识符返回
    - **Property 5: 子文档标识符返回**
    - **Validates: Requirements 2.3**
  
  - [ ]* 11.4 编写属性测试：子文档创建容错性
    - **Property 6: 子文档创建容错性**
    - **Validates: Requirements 2.4, 8.4**
  
  - [ ]* 11.5 编写属性测试：处理结果摘要
    - **Property 15: 处理结果摘要**
    - **Validates: Requirements 8.5**

- [ ] 12. 实现主函数和日志记录
  - [ ] 12.1 创建 `write_to_feishu_docx()` 主函数
    - 加载配置
    - 初始化所有组件
    - 协调整体流程
    - 返回处理结果
    - _Requirements: 1.1, 2.1, 8.5_
  
  - [ ] 12.2 实现日志记录
    - 配置 Python logging 模块
    - 在关键操作点添加日志
    - 记录错误详情（API 错误、LLM 错误等）
    - _Requirements: 8.1, 8.2, 8.3_
  
  - [ ]* 12.3 编写属性测试：错误日志记录
    - **Property 16: 错误日志记录**
    - **Validates: Requirements 8.1, 8.2, 8.3**

- [ ] 13. 集成测试
  - [ ]* 13.1 编写端到端集成测试
    - 使用 mock 飞书 API 和 LLM
    - 测试完整的处理流程
    - 测试各种内容组合（博客、视频、混合）
    - 测试部分失败场景
    - 验证文档层次结构
    - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.2, 5.1, 5.2, 5.3, 5.4_

- [ ] 14. 创建命令行接口（可选）
  - 创建 CLI 脚本用于测试和手动执行
  - 支持从文件读取输入数据
  - 支持配置参数覆盖
  - _Requirements: 1.1_

- [ ] 15. 最终检查点 - 确保所有功能正常
  - 运行所有测试（单元测试 + 属性测试）
  - 检查代码覆盖率（目标 > 80%）
  - 运行 linting 和类型检查
  - 如有问题请询问用户

## Notes

- 任务标记 `*` 的为可选测试任务，可以跳过以加快 MVP 开发
- 每个任务都引用了具体的需求编号，确保可追溯性
- 检查点任务确保增量验证，及时发现问题
- 属性测试验证通用正确性，单元测试验证特定场景
- 使用 mock 对象隔离外部依赖（飞书 API、LLM、HTTP 请求）
