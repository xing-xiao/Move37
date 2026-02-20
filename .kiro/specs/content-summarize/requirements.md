# 需求文档

## 简介

内容摘要功能旨在对从 RSS 订阅源和 YouTube 频道收集的内容进行自动化摘要生成，作为每日的 AI 咨询简报。系统将处理 `collect_all` 函数返回的 URL 列表，直接将 URL 传递给大语言模型，生成包含简介和深度总结的摘要内容。

## 术语表

- **Content_Summarizer**: 内容摘要系统，负责协调整个摘要生成流程
- **LLM_Client**: 大语言模型客户端，负责调用 LLM API 生成摘要
- **Collection_Result**: 由 `collect_all` 函数返回的数据结构，包含待处理的 URL 列表
- **Summary_Result**: 摘要结果数据结构，包含原始信息、简介、概要、处理时间、使用模型和消耗 token 数
- **Brief**: 简介，100 字以内的内容概述
- **Summary**: 概要，1000 字以内的深度总结

## 需求

### 需求 1: 处理收集结果

**用户故事:** 作为系统用户，我希望能够处理 `collect_all` 返回的结果，以便对所有收集到的内容进行摘要。

#### 验收标准

1. WHEN 提供有效的 Collection_Result 数据 THEN THE Content_Summarizer SHALL 解析并提取所有 URL 项
2. WHEN Collection_Result 包含多个来源类型 THEN THE Content_Summarizer SHALL 处理所有支持的来源类型（Blogs 和 YouTube Channels）
3. WHEN Collection_Result 中某个来源的 success 字段为 false THEN THE Content_Summarizer SHALL 跳过该来源并记录警告
4. WHEN Collection_Result 为空或不包含任何项 THEN THE Content_Summarizer SHALL 返回空的摘要结果列表

### 需求 2: 生成内容摘要

**用户故事:** 作为系统用户，我希望使用大语言模型直接从 URL 生成内容摘要，以便快速了解文章或视频的核心内容。

#### 验收标准

1. WHEN 提供有效的 URL THEN THE LLM_Client SHALL 使用指定的提示词模板调用 LLM API
2. WHEN 调用 LLM API THEN THE LLM_Client SHALL 在提示词中包含 URL 并要求生成简介和深度总结
3. WHEN 生成摘要 THEN THE LLM_Client SHALL 确保简介长度在 100 字以内
4. WHEN 生成摘要 THEN THE LLM_Client SHALL 确保深度总结长度在 1000 字以内
5. WHEN 生成摘要 THEN THE LLM_Client SHALL 使用中文输出所有内容
6. IF LLM API 调用失败或超时 THEN THE LLM_Client SHALL 重试最多 3 次
7. IF 所有重试均失败 THEN THE LLM_Client SHALL 返回错误信息并标记摘要生成失败

### 需求 3: 记录处理元数据

**用户故事:** 作为系统用户，我希望记录每次处理的元数据，以便监控系统性能和成本。

#### 验收标准

1. WHEN 处理每个 URL THEN THE Content_Summarizer SHALL 记录处理开始时间
2. WHEN 完成处理 THEN THE Content_Summarizer SHALL 计算并记录处理耗时
3. WHEN 调用 LLM API THEN THE Content_Summarizer SHALL 记录使用的模型名称
4. WHEN 接收 LLM 响应 THEN THE Content_Summarizer SHALL 记录消耗的 token 数量
5. WHEN 生成结果 THEN THE Content_Summarizer SHALL 将所有元数据包含在输出中

### 需求 4: 输出摘要结果

**用户故事:** 作为系统用户，我希望获得结构化的摘要结果，以便后续处理和存储。

#### 验收标准

1. WHEN 完成所有 URL 的处理 THEN THE Content_Summarizer SHALL 返回包含所有摘要的结果列表
2. WHEN 生成摘要结果 THEN THE Content_Summarizer SHALL 保留原始的来源信息（source_type、source_title）
3. WHEN 生成摘要结果 THEN THE Content_Summarizer SHALL 包含原始 URL、标题、发布时间
4. WHEN 生成摘要结果 THEN THE Content_Summarizer SHALL 添加 processing_time、model_used、tokens_consumed、brief 和 summary 字段
5. WHEN 某个 URL 处理失败 THEN THE Content_Summarizer SHALL 在结果中标记失败状态并包含错误信息
6. WHEN 生成最终结果 THEN THE Content_Summarizer SHALL 以 JSON 格式输出，保持与输入结构的一致性

### 需求 5: 错误处理和日志记录

**用户故事:** 作为系统维护者，我希望系统能够妥善处理错误并记录详细日志，以便排查问题和监控系统运行状态。

#### 验收标准

1. WHEN 发生任何错误 THEN THE Content_Summarizer SHALL 记录详细的错误日志，包含错误类型、URL 和错误消息
2. WHEN 处理每个 URL THEN THE Content_Summarizer SHALL 记录处理开始和完成的信息日志
3. IF 单个 URL 处理失败 THEN THE Content_Summarizer SHALL 继续处理其他 URL 而不中断整个流程
4. WHEN 网络请求失败 THEN THE Content_Summarizer SHALL 记录网络错误并包含 HTTP 状态码
5. WHEN LLM API 调用失败 THEN THE Content_Summarizer SHALL 记录 API 错误详情和重试次数

### 需求 6: 配置管理

**用户故事:** 作为系统配置者，我希望能够配置 LLM API 参数和提示词模板，以便适应不同的使用场景。

#### 验收标准

1. THE Content_Summarizer SHALL 支持通过环境变量或配置文件配置 LLM API 密钥
2. THE Content_Summarizer SHALL 支持配置 LLM 模型名称和参数（如温度、最大令牌数）
3. THE Content_Summarizer SHALL 支持配置提示词模板
4. THE Content_Summarizer SHALL 支持配置 API 重试次数和超时时间
5. WHERE 未提供配置 THEN THE Content_Summarizer SHALL 使用合理的默认值
