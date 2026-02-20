# Content Summarize

`move37.summarize` 用于对 `collect_all()` 采集出的 URL 列表做批量摘要，输出中文 `brief`（<=100字）和 `summary`（<=1000字），并补充处理元数据。

YouTube 链接会先抓取内容再总结：

- 优先抓取字幕（transcript）
- 字幕不可用时回退到元数据（metadata-only）
- 超长字幕会先分块摘要，再汇总为最终摘要
- Gemini 模型不可用时会自动尝试可用的 fallback 模型

## 1. 模块结构

- `src/move37/summarize/config.py`: 配置加载与校验
- `src/move37/summarize/llm_client.py`: 多 Provider LLM 调用、重试、响应解析
- `src/move37/summarize/summarizer.py`: `summarize_single_url()` 与 `summarize_all()`
- `src/samples/summarize/summarize.py`: 可直接运行的示例入口

## 2. 安装依赖

在项目根目录执行：

```bash
pip install -r requirements.txt
```

## 3. 配置 `.env`

先复制模板：

```bash
cp .env.example .env
```

然后按你使用的 Provider 填写配置。

### 3.1 配置示例（OpenAI）

```bash
LLM_PROVIDER=openai

LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2000
LLM_TIMEOUT=60
LLM_MAX_RETRIES=3

LLM_OPENAI_API_KEY=sk-xxx
LLM_OPENAI_MODEL=gpt-3.5-turbo
LLM_OPENAI_BASE_URL=https://api.openai.com/v1
```

### 3.2 配置示例（DeepSeek）

```bash
LLM_PROVIDER=deepseek
LLM_DEEPSEEK_API_KEY=sk-xxx
LLM_DEEPSEEK_MODEL=deepseek-chat
LLM_DEEPSEEK_BASE_URL=https://api.deepseek.com
```

### 3.3 配置示例（Gemini）

```bash
LLM_PROVIDER=gemini
LLM_GEMINI_API_KEY=AIza...
LLM_GEMINI_MODEL=gemini-2.5-flash
# Gemini 通常不需要 BASE_URL
LLM_GEMINI_BASE_URL=
```

### 3.4 配置示例（GLM）

```bash
LLM_PROVIDER=glm
LLM_GLM_API_KEY=your-glm-key
LLM_GLM_MODEL=glm-4
LLM_GLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4/
```

### 3.5 可选提示词

```bash
LLM_PROMPT_TEMPLATE=...{url}...
```

注意：`LLM_PROMPT_TEMPLATE` 必须包含 `{url}` 占位符。  
如需让模型直接基于预抓取内容总结，可在模板中加入 `{content}` 占位符。

### 3.6 YouTube 预处理配置

```bash
# 字幕语言优先级（逗号分隔）
YOUTUBE_TRANSCRIPT_LANGS=zh-Hans,zh,en
# 传给摘要模型的最大字符数
YOUTUBE_MAX_INPUT_CHARS=20000
# 超过该值启用分块摘要
YOUTUBE_CHUNK_SIZE=4000
# 字幕不可用时是否回退到 metadata-only 总结
YOUTUBE_ENABLE_METADATA_FALLBACK=true
```

## 4. 配置加载规则

`load_config()` 的优先级：

1. 代码传入 `config` 参数
2. `.env` 文件
3. 默认值（`config.py` 中 `DEFAULT_CONFIG` 和 `PROVIDER_CONFIGS`）

Provider 选择与读取规则：

1. 读取 `LLM_PROVIDER`（`openai|deepseek|gemini|glm`）
2. 根据 provider 读取对应键：
   - `LLM_<PROVIDER>_API_KEY`（必填）
   - `LLM_<PROVIDER>_MODEL`
   - `LLM_<PROVIDER>_BASE_URL`
3. 通用参数始终读取：
   - `LLM_TEMPERATURE`
   - `LLM_MAX_TOKENS`
   - `LLM_TIMEOUT`
   - `LLM_MAX_RETRIES`
4. YouTube 预处理参数：
   - `YOUTUBE_TRANSCRIPT_LANGS`
   - `YOUTUBE_MAX_INPUT_CHARS`
   - `YOUTUBE_CHUNK_SIZE`
   - `YOUTUBE_ENABLE_METADATA_FALLBACK`

## 5. 运行方式

### 5.1 运行示例 CLI

在项目根目录执行：

```bash
PYTHONPATH=src python src/samples/summarize/summarize.py
```

可选参数：

- `--provider openai|deepseek|gemini|glm`
- `--model <model_name>`
- `--api-key <api_key>`
- `--url <single_url>`（覆盖示例里的第一条 URL）

例如：

```bash
PYTHONPATH=src python src/samples/summarize/summarize.py --provider deepseek --api-key sk-xxx
```

### 5.2 在代码中调用

```python
from move37.ingest.collection import collect_all
from move37.summarize import summarize_all

collection_result = collect_all(target_date="2026-02-19")
summary_result = summarize_all(collection_result)
```

也可以覆盖部分配置：

```python
summary_result = summarize_all(
    collection_result,
    config={
        "provider": "openai",
        "api_key": "sk-xxx",
        "model": "gpt-4-turbo",
        "max_retries": 3,
    },
)
```

## 6. 输入输出格式

输入：`collect_all()` 返回的结构（`results[*].items[*].url` 等字段）。

输出：在每个 `item` 追加字段：

- `processing_time`
- `model_used`
- `tokens_consumed`
- `brief`
- `summary`
- `success`
- `error`（失败时）

当来源 `success=false` 时会跳过该来源；当单条 URL 失败时不会中断整体流程。

YouTube 项额外可能包含：

- `summary_basis`: `transcript` 或 `metadata`
- `youtube_video_id`
- `warning`（例如字幕不可用，已降级到 metadata-only）

## 7. 日志与重试

- 重试策略：指数退避（1s、2s、4s...）
- 日志级别：
  - `INFO`: 开始、进度、成功
  - `WARNING`: 重试、截断、跳过
  - `ERROR`: 最终失败、异常

## 8. 常见错误

- `Missing API key for provider ...`
  - 原因：未在 `.env` 配置 `LLM_<PROVIDER>_API_KEY`
- `Unsupported provider ...`
  - 原因：`LLM_PROVIDER` 不在 `openai|deepseek|gemini|glm`
- ``prompt_template` must include `{url}` placeholder.`
  - 原因：`LLM_PROMPT_TEMPLATE` 未包含 `{url}`
