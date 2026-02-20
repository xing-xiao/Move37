# 实现计划: 内容摘要

## 概述

本实现计划将内容摘要功能分解为一系列增量式的编码任务。系统采用三层架构（主协调器、URL 处理函数、LLM 客户端），支持多个 LLM 提供商（OpenAI、DeepSeek、Gemini、GLM），直接将 URL 传递给 LLM 生成中文摘要，包括简介和深度总结。

## 任务

- [ ] 1. 创建项目结构和配置管理
  - 创建 `src/move37/summarize/` 目录结构
  - 创建 `__init__.py` 文件，在其中调用 `load_dotenv()` 加载 .env 文件
  - 创建 `.env.example` 文件作为配置模板
  - 实现 `config.py` 模块，包含 `load_config()` 函数和默认配置
  - 在 `load_config()` 中使用 `python-dotenv` 的 `load_dotenv()` 加载 .env 文件
  - 定义 `DEFAULT_CONFIG` 字典（包含 provider、model、temperature、max_tokens、timeout、max_retries、prompt_template）
  - 定义 `PROVIDER_CONFIGS` 字典（包含各提供商的 base_url）
  - 所有LLM相关配置均从`.env`文件读取，不从环境变量加载配置（LLM_PROVIDER、LLM_API_KEY、LLM_MODEL 等）
  - 根据LLM_PROVIDER的结果，读取`.env`中相应的provider的API KEY、MODEL、BASE_URL等内容
  - 如果 API 密钥缺失，抛出 `ConfigurationError` 异常
  - _需求: 6.1, 6.2, 6.3, 6.4, 6.5_

- [ ]* 1.1 编写配置管理的单元测试
  - 测试默认配置加载
  - 测试环境变量覆盖
  - 测试配置优先级
  - 测试缺少 API 密钥时的错误处理
  - _需求: 6.1, 6.2, 6.3, 6.4, 6.5_

- [ ] 2. 实现 LLM 客户端基础架构
  - [ ] 2.1 创建 `llm_client.py` 模块并实现 LLMClient 类
    - 实现 `__init__()` 方法，接受 provider、api_key、model、base_url、temperature、max_tokens、timeout、max_retries 参数
    - 实现 `generate_summary()` 方法，接受 url 和 prompt_template 参数
    - 实现 `exponential_backoff()` 函数（指数退避重试策略）
    - 实现重试逻辑（最多 3 次，使用指数退避）
    - 实现响应解析逻辑（从 JSON 格式提取 brief 和 summary）
    - 返回包含 brief、summary、model_used、tokens_consumed、success、error 的字典
    - _需求: 2.1, 2.2, 2.6, 2.7_

  - [ ]* 2.2 编写 LLM 客户端基础功能的单元测试
    - 测试指数退避计算
    - 测试重试机制（使用 mock）
    - 测试响应解析
    - 测试超时处理
    - 测试错误处理
    - _需求: 2.6, 2.7_

- [ ] 3. 实现 OpenAI 提供商支持
  - [ ] 3.1 在 LLMClient 中添加 OpenAI 特定实现
    - 使用 `openai` Python SDK
    - 在 `generate_summary()` 中检测 provider="openai"
    - 配置 OpenAI 客户端（api_key、base_url）
    - 调用 `client.chat.completions.create()` 方法
    - 处理 OpenAI API 响应格式
    - 从响应中提取 token 使用信息（prompt_tokens + completion_tokens）
    - _需求: 2.1, 2.2, 2.3, 2.4, 2.5_

  - [ ]* 3.2 编写 OpenAI 客户端的单元测试
    - 测试成功调用场景（使用 mock）
    - 测试 API 错误处理
    - 测试 token 计数提取
    - _需求: 2.1, 2.2_

- [ ] 4. 实现 DeepSeek 提供商支持
  - [ ] 4.1 在 LLMClient 中添加 DeepSeek 特定实现
    - 使用 OpenAI 兼容接口（openai SDK）
    - 配置 base_url 为 "https://api.deepseek.com"
    - 处理 DeepSeek 特定的响应格式差异（如有）
    - _需求: 2.1, 2.2, 2.3, 2.4, 2.5_

  - [ ]* 4.2 编写 DeepSeek 客户端的单元测试
    - 测试 API 调用（使用 mock）
    - 测试响应处理
    - _需求: 2.1, 2.2_

- [ ] 5. 实现 Gemini 提供商支持
  - [ ] 5.1 在 LLMClient 中添加 Gemini 特定实现
    - 使用 `google-generativeai` SDK
    - 在 `generate_summary()` 中检测 provider="gemini"
    - 配置 Gemini 客户端（api_key）
    - 调用 `model.generate_content()` 方法
    - 处理 Gemini API 响应格式
    - 适配 Gemini 的 token 计数方式
    - _需求: 2.1, 2.2, 2.3, 2.4, 2.5_

  - [ ]* 5.2 编写 Gemini 客户端的单元测试
    - 测试 API 调用（使用 mock）
    - 测试响应处理
    - _需求: 2.1, 2.2_

- [ ] 6. 实现 GLM 提供商支持
  - [ ] 6.1 在 LLMClient 中添加 GLM 特定实现
    - 使用 OpenAI 兼容接口（openai SDK）
    - 配置 base_url 为 "https://open.bigmodel.cn/api/paas/v4/"
    - 处理 GLM 特定的响应格式差异（如有）
    - _需求: 2.1, 2.2, 2.3, 2.4, 2.5_

  - [ ]* 6.2 编写 GLM 客户端的单元测试
    - 测试 API 调用（使用 mock）
    - 测试响应处理
    - _需求: 2.1, 2.2_

- [ ] 7. 检查点 - 确保所有 LLM 客户端测试通过
  - 确保所有测试通过，如有问题请询问用户

- [ ] 8. 实现响应验证和长度约束
  - [ ] 8.1 在 LLMClient 中添加响应验证逻辑
    - 在 `generate_summary()` 中验证响应格式
    - 检查 brief 和 summary 字段是否存在
    - 验证 brief 长度不超过 100 字符
    - 验证 summary 长度不超过 1000 字符
    - 如果超长，进行截断并记录 WARNING 日志
    - 处理响应解析错误（JSON 格式不正确）
    - _需求: 2.3, 2.4_

  - [ ]* 8.2 编写响应验证的单元测试
    - 测试长度验证
    - 测试截断逻辑
    - 测试 JSON 解析错误处理
    - _需求: 2.3, 2.4_

  - [ ]* 8.3 编写属性测试：简介长度约束
    - **属性 6: 简介长度约束**
    - **验证需求: 2.3**

  - [ ]* 8.4 编写属性测试：概要长度约束
    - **属性 7: 概要长度约束**
    - **验证需求: 2.4**

  - [ ]* 8.5 编写属性测试：中文输出
    - **属性 9: 中文输出**
    - **验证需求: 2.5**

- [ ] 9. 实现单个 URL 处理函数
  - [ ] 9.1 创建 `summarizer.py` 模块并实现 summarize_single_url() 函数
    - 接受 url、title、llm_client、prompt_template 参数
    - 使用 `time.time()` 记录处理开始时间
    - 调用 `llm_client.generate_summary(url, prompt_template)`
    - 计算处理耗时（结束时间 - 开始时间）
    - 格式化处理时间为字符串（如 "2.3s"）
    - 收集所有元数据（processing_time、model_used、tokens_consumed、brief、summary）
    - **使用 logging.info() 打印处理结果（URL、标题、处理时间、token 消耗、简介预览前 50 字符）**
    - 处理异常并返回包含 error 字段的字典
    - _需求: 3.1, 3.2, 3.3, 3.4, 3.5, 5.1, 5.2_

  - [ ]* 9.2 编写单个 URL 处理函数的单元测试
    - 测试成功场景
    - 测试失败场景
    - 测试处理时间计算和格式化
    - 测试元数据收集
    - 测试日志输出
    - _需求: 3.2, 3.5_

  - [ ]* 9.3 编写属性测试：处理时间格式
    - **属性 10: 处理时间格式**
    - **验证需求: 3.2**

- [ ] 10. 实现主协调函数
  - [ ] 10.1 在 summarizer.py 中实现 summarize_all() 函数
    - 接受 collection_result 和可选的 config 参数
    - 调用 `load_config(config)` 加载配置
    - 验证 API 密钥存在，否则抛出 ConfigurationError
    - 创建 LLMClient 实例
    - 深拷贝 collection_result 以避免修改原始数据
    - 遍历 results 数组中的每个来源
    - 检查 success 字段，跳过 success=false 的来源并记录 WARNING 日志
    - 对每个 URL 项调用 `summarize_single_url()`
    - 将返回的摘要字段添加到 item 中
    - 记录处理进度 INFO 日志（如 "处理 1/10"）
    - 返回增强后的结果
    - _需求: 1.1, 1.2, 1.3, 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 5.2_

  - [ ]* 10.2 编写主协调函数的单元测试
    - 测试完整流程（使用 mock LLMClient）
    - 测试空输入处理
    - 测试部分失败场景
    - 测试 success=false 来源跳过
    - _需求: 1.1, 1.2, 1.3, 1.4_

  - [ ]* 10.3 编写属性测试：结构保持性
    - **属性 1: 结构保持性**
    - **验证需求: 1.1, 1.2, 4.1, 4.2**

  - [ ]* 10.4 编写属性测试：URL 完整性
    - **属性 2: URL 完整性**
    - **验证需求: 1.1, 1.2, 4.1**

  - [ ]* 10.5 编写属性测试：失败来源跳过
    - **属性 3: 失败来源跳过**
    - **验证需求: 1.3**

  - [ ]* 10.6 编写属性测试：空输入处理
    - **属性 4: 空输入处理**
    - **验证需求: 1.4**

  - [ ]* 10.7 编写属性测试：元数据完整性
    - **属性 5: 元数据完整性**
    - **验证需求: 3.1, 3.2, 3.3, 3.4, 3.5, 4.4**

  - [ ]* 10.8 编写属性测试：错误隔离性
    - **属性 8: 错误隔离性**
    - **验证需求: 5.3**

- [ ] 11. 实现日志记录
  - [ ] 11.1 在所有模块中配置和添加日志记录
    - 在 `__init__.py` 中配置 Python logging（格式、级别）
    - 在 LLMClient 中添加日志：API 调用开始、成功、失败、重试
    - 在 summarize_single_url 中添加日志：处理开始、完成、错误
    - 在 summarize_all 中添加日志：处理开始、进度、完成、跳过来源
    - 确保日志包含上下文信息（URL、错误类型、HTTP 状态码等）
    - 使用适当的日志级别（INFO、WARNING、ERROR）
    - _需求: 5.1, 5.2, 5.4, 5.5_

  - [ ]* 11.2 编写日志记录的单元测试
    - 验证日志内容
    - 验证日志级别
    - 使用 caplog fixture 捕获日志
    - _需求: 5.1, 5.2_

- [ ] 12. 检查点 - 确保所有核心功能测试通过
  - 确保所有测试通过，如有问题请询问用户

- [ ] 13. 创建主入口程序
  - [ ] 13.1 创建 src/samples/summarize/ 目录和主程序
    - 创建 `src/samples/summarize/` 目录
    - 创建 `src/samples/summarize/__init__.py`
    - 创建 `src/samples/summarize/summarize.py` 主程序
    - 实现 `main()` 函数作为功能入口
    - 包含测试用的 Collection_Result JSON 数据（模拟 `collect_all()` 返回值）
    - 使用 argparse 支持命令行参数：--provider、--model、--api-key
    - 调用 `summarize_all()` 函数
    - 使用 `json.dumps()` 格式化输出处理结果
    - 添加 `if __name__ == "__main__":` 入口
    - _需求: 无（测试程序）_

  - [ ] 13.2 测试主入口程序
    - 手动运行程序验证功能
    - 测试不同的命令行参数组合
    - _需求: 无（测试程序）_

- [ ] 14. 添加项目依赖
  - [ ] 14.1 更新 requirements.txt 或 pyproject.toml
    - 添加 `openai>=1.0.0`
    - 添加 `google-generativeai>=0.3.0`
    - 添加 `pytest>=7.0.0`
    - 添加 `pytest-cov>=4.0.0`
    - 添加 `hypothesis>=6.0.0`
    - 添加 `python-dotenv>=1.0.0`（用于 .env 文件支持）
    - _需求: 无（依赖管理）_

- [ ] 15. 创建文档和示例
  - [ ] 15.1 创建 README 文档
    - 在 `src/move37/summarize/` 目录创建 README.md
    - 说明功能概述和架构
    - 说明支持的 LLM 提供商和推荐模型
    - 提供配置示例（.env 文件和代码配置）
    - 说明 .env 文件的使用方法和配置优先级
    - 说明如何运行主入口程序
    - 提供使用示例代码
    - _需求: 无（文档）_

  - [ ] 15.2 验证 .env.example 文件
    - 确保 .env.example 包含所有支持的环境变量
    - 添加详细的注释说明每个变量的用途
    - 提供不同 LLM 提供商的配置示例
    - _需求: 无（文档）_

- [ ] 16. 最终检查点 - 运行所有测试并验证功能
  - 运行所有单元测试：`pytest tests/`
  - 运行所有属性测试（确保至少 100 次迭代）
  - 检查代码覆盖率：`pytest --cov=move37.summarize --cov-report=html`
  - 验证覆盖率 > 80%
  - 确保所有测试通过，如有问题请询问用户

## 注意事项

- 标记 `*` 的任务是可选的，可以跳过以加快 MVP 开发
- 每个任务都引用了具体的需求以便追溯
- 检查点确保增量验证
- 属性测试验证通用正确性属性（每个测试至少 100 次迭代）
- 单元测试验证具体示例和边缘情况
- 系统采用三层架构：summarize_all（协调器）→ summarize_single_url（URL 处理）→ LLMClient（LLM 调用）
