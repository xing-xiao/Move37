# Requirements Document

## Introduction

本文档定义了飞书知识库文档写入系统的需求。该系统将飞书机器人推送的内容自动写入飞书知识库，为每个内容项创建结构化文档，并对博客文章生成翻译和公众号文章。

## Glossary

- **System**: 飞书知识库文档写入系统
- **Feishu_Bot**: 飞书机器人应用
- **Knowledge_Base**: 飞书知识库
- **Main_Document**: 以日期为标题的主文档
- **Sub_Document**: 主文档下的子文档
- **Content_Item**: 飞书机器人推送的单个内容项（博客文章或YouTube视频）
- **Blog_Article**: 博客类型的内容项
- **YouTube_Video**: YouTube视频类型的内容项
- **Translation_Document**: 翻译文章的子文档
- **WeChat_Article_Document**: 公众号文章的子文档
- **Target_Date**: 内容推送的目标日期
- **Wiki_Space_ID**: 飞书知识库 Space ID
- **Parent_Node_Token**: 写入文档的父节点 token

## Requirements

### Requirement 1: 创建主文档

**User Story:** 作为系统管理员，我希望系统能够为每个日期创建主文档，以便组织和管理每日推送的内容。

#### Acceptance Criteria

1. WHEN 系统接收到推送内容 THEN THE System SHALL 在 Knowledge_Base 中创建一个 Main_Document
2. WHEN 创建 Main_Document THEN THE System SHALL 使用 Target_Date 作为文档标题
3. WHEN 创建 Main_Document THEN THE System SHALL 在 Wiki_Space_ID 和 Parent_Node_Token 指定的位置创建文档
4. WHEN 创建 Main_Document 失败 THEN THE System SHALL 记录错误信息并返回失败状态

### Requirement 2: 创建内容项子文档

**User Story:** 作为内容管理者，我希望每个内容项都有独立的子文档，以便详细查看每篇文章的信息和总结。

#### Acceptance Criteria

1. WHEN 处理 Content_Item THEN THE System SHALL 在 Main_Document 下创建 Sub_Document
2. WHEN 创建 Sub_Document THEN THE System SHALL 使用内容项的标题作为子文档标题
3. WHEN Sub_Document 创建成功 THEN THE System SHALL 返回子文档的唯一标识符
4. WHEN Sub_Document 创建失败 THEN THE System SHALL 记录错误并继续处理其他内容项

### Requirement 3: 填充子文档基本信息

**User Story:** 作为内容阅读者，我希望子文档包含完整的文章元信息，以便快速了解文章来源和基本情况。

#### Acceptance Criteria

1. WHEN 填充 Sub_Document THEN THE System SHALL 包含文章标题作为一级标题
2. WHEN 填充 Sub_Document THEN THE System SHALL 包含来源信息（作者或频道名称）
3. WHEN 填充 Sub_Document THEN THE System SHALL 包含原文链接
4. WHEN 填充 Sub_Document THEN THE System SHALL 包含发布时间
5. WHEN 填充 Sub_Document THEN THE System SHALL 包含消耗的Token数量
6. WHEN 填充 Sub_Document THEN THE System SHALL 包含文章简介内容
7. WHEN 填充 Sub_Document THEN THE System SHALL 包含处理结果状态（成功或失败）
8. IF 处理失败 THEN THE System SHALL 在文章概括中包含失败原因

### Requirement 4: 填充文章总结

**User Story:** 作为内容阅读者，我希望子文档包含文章总结，以便快速了解文章核心内容。

#### Acceptance Criteria

1. WHEN 填充 Sub_Document THEN THE System SHALL 包含"文章总结"章节作为二级标题
2. WHEN 填充文章总结章节 THEN THE System SHALL 使用 Content_Item 的 summary 字段内容
3. WHEN summary 字段为空 THEN THE System SHALL 在总结章节中标注"无总结内容"

### Requirement 5: 处理博客文章的翻译和公众号文章

**User Story:** 作为内容管理者，我希望博客文章能够生成翻译和公众号版本，以便扩展内容的使用场景。

#### Acceptance Criteria

1. WHEN Content_Item 是 Blog_Article THEN THE System SHALL 创建 Translation_Document 作为 Sub_Document 的子文档
2. WHEN Content_Item 是 Blog_Article THEN THE System SHALL 创建 WeChat_Article_Document 作为 Sub_Document 的子文档
3. WHEN Content_Item 是 YouTube_Video THEN THE System SHALL NOT 创建 Translation_Document
4. WHEN Content_Item 是 YouTube_Video THEN THE System SHALL NOT 创建 WeChat_Article_Document
5. WHEN 创建翻译或公众号文档 THEN THE System SHALL 在 Sub_Document 中包含对应子文档的链接

### Requirement 6: 生成翻译文章

**User Story:** 作为内容阅读者，我希望博客文章能够提供中英对照翻译，以便更好地理解原文内容。

#### Acceptance Criteria

1. WHEN 生成 Translation_Document THEN THE System SHALL 提取 Blog_Article 的原文内容
2. WHEN 翻译文章内容 THEN THE System SHALL 使用 LLM 按段落进行翻译
3. WHEN 格式化翻译内容 THEN THE System SHALL 将原文段落放在上方，中文翻译放在下方
4. WHEN 翻译完成 THEN THE System SHALL 将翻译内容写入 Translation_Document
5. WHEN 翻译失败 THEN THE System SHALL 在 Translation_Document 中记录失败原因

### Requirement 7: 生成公众号文章

**User Story:** 作为内容运营者，我希望系统能够自动生成适合公众号发布的文章版本，以便快速进行内容分发。

#### Acceptance Criteria

1. WHEN 生成 WeChat_Article_Document THEN THE System SHALL 提取 Blog_Article 的内容
2. WHEN 生成公众号文章 THEN THE System SHALL 使用 LLM 对内容进行总结和改写
3. WHEN 生成公众号文章 THEN THE System SHALL 确保文章风格适合AI咨询类公众号
4. WHEN 生成完成 THEN THE System SHALL 将生成的文章写入 WeChat_Article_Document
5. WHEN 生成失败 THEN THE System SHALL 在 WeChat_Article_Document 中记录失败原因

### Requirement 8: 错误处理和日志记录

**User Story:** 作为系统管理员，我希望系统能够妥善处理错误并记录详细日志，以便排查问题和监控系统运行状态。

#### Acceptance Criteria

1. WHEN 任何操作失败 THEN THE System SHALL 记录详细的错误信息到日志
2. WHEN 飞书API调用失败 THEN THE System SHALL 记录API错误代码和错误消息
3. WHEN LLM调用失败 THEN THE System SHALL 记录失败原因和重试次数
4. WHEN 单个 Content_Item 处理失败 THEN THE System SHALL 继续处理其他内容项
5. WHEN 所有内容项处理完成 THEN THE System SHALL 返回处理结果摘要（成功数量、失败数量）

### Requirement 9: 文档格式规范

**User Story:** 作为内容阅读者，我希望所有文档遵循统一的格式规范，以便获得一致的阅读体验。

#### Acceptance Criteria

1. THE System SHALL 使用Markdown格式编写所有文档内容
2. WHEN 创建标题 THEN THE System SHALL 使用正确的标题层级（一级、二级、三级）
3. WHEN 创建列表 THEN THE System SHALL 使用无序列表格式（* 或 -）
4. WHEN 插入链接 THEN THE System SHALL 使用Markdown链接格式
5. WHEN 文档内容包含特殊字符 THEN THE System SHALL 正确转义以避免格式错误

### Requirement 10: 飞书 Wiki 接口与配置

**User Story:** 作为系统管理员，我希望系统严格使用飞书 Wiki 指定接口并基于固定配置写入文档，以便实现稳定可维护的知识库同步。

#### Acceptance Criteria

1. WHEN System 创建文档节点 THEN THE System SHALL 调用 `https://open.feishu.cn/document/server-docs/docs/wiki-v2/space-node/create` 接口
2. WHEN System 写入文档内容 THEN THE System SHALL 调用 `https://open.feishu.cn/document/docs/docs/document-block/create-2` 接口
3. WHEN System 加载配置 THEN THE System SHALL 要求 `FEISHU_WIKI_SPACE_ID` 和 `FEISHU_WIKI_PARENT_NODE_TOKEN` 为必需项
4. WHEN `FEISHU_WIKI_SPACE_ID` 或 `FEISHU_WIKI_PARENT_NODE_TOKEN` 缺失 THEN THE System SHALL 抛出配置错误并停止执行
