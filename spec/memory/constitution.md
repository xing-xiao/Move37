# Move37 Project Constitution

## 1. 技术栈(The "Must-Haves")

- **Language**: Python 3.10+.

## 2. Python Code Style Specification (Python 代码风格规范)

本规范旨在确保代码库的一致性、可读性和可维护性。所有提交至本项目的 Python 代码**必须**遵守以下约束。

### 2.1 核心格式化标准 (Core Formatting)
> **原则**：格式化问题不应由人工审查，应由工具自动处理。

- **基准标准**：必须遵守 [PEP 8](https://peps.python.org/pep-0008/) 规范。
- **代码格式化工具**：项目强制使用 **[Black](https://github.com/psf/black)** 作为唯一的格式化工具。
    *   **缩进**：必须使用 **4个空格**，严禁使用 Tab。
    *   **行宽 (Line Length)**：限制为 **88 字符** (Black 默认标准)，特殊情况（如长 URL）除外。
    *   **引号**：默认使用 **双引号 (`"`)**，仅当字符串内部包含双引号时才使用单引号以避免转义。
- **空行**：
    *   顶层函数和类定义之间保留 **2个空行**。
    *   类内部的方法定义之间保留 **1个空行**。

### 2.2 命名公约 (Naming Conventions)

| 实体类型 | 命名风格 | 示例 | 备注 |
| :--- | :--- | :--- | :--- |
| **变量 / 参数** | `snake_case` | `user_id`, `is_valid` | 避免单字符命名 (如 `x`, `y`)，除非在数学计算或简短循环中。 |
| **函数 / 方法** | `snake_case` | `get_user_data()` | 动词开头，描述操作。 |
| **类 (Class)** | `PascalCase` | `UserProfile`, `HTTPClient` | 名词形式。 |
| **常量** | `UPPER_CASE` | `MAX_RETRY_COUNT`, `DEFAULT_TIMEOUT` | 单词间用下划线分隔。 |
| **模块 (文件名)** | `snake_case` | `data_loader.py` | 全小写，尽量简短。 |
| **私有成员** | `_leading_underscore` | `_internal_cache` | 仅限类内部或模块内部使用。 |

- **禁止项**：
    *   禁止使用 `l` (小写L), `O` (大写O), `I` (大写I) 作为单字符变量名，以防与数字混淆。
    *   禁止使用 Python 内置关键字（如 `list`, `dict`, `type`, `id`）作为变量名。

### 2.3 类型注解 (Type Hinting)
> **原则**：代码即文档，静态类型检查是质量的第一道防线。

- **强制范围**：所有公开接口（Public APIs）、函数参数、返回值**必须**包含类型注解。
- **工具**：代码必须通过 **[mypy](http://mypy-lang.org/)** 或 **[pyright](https://github.com/microsoft/pyright)** 的静态检查（`strict` 模式）。
- **泛型与集合**：
    *   Python 3.9+：直接使用内置类型 (`list[str]`, `dict[str, int]`)，不再使用 `typing.List`。
    *   复杂类型使用 `typing.Optional`, `typing.Union`, `typing.Any` (慎用 Any)。

### 2.4 导入规范 (Imports)

- **排序工具**：必须使用 **[isort](https://pycqa.github.io/isort/)** 或 **Ruff** 进行自动排序。
- **顺序**：
    1.  标准库 (Standard Library)
    2.  第三方库 (Third Party)
    3.  本地应用/库 (Local Application/Library)
- **样式**：
    *   **推荐**：使用绝对导入 (`from my_project.models import User`)。
    *   **禁止**：禁止使用通配符导入 (`from module import *`)，这会污染命名空间且难以追踪。
    *   **每行**：每行仅导入一个模块，或使用括号分组。

### 2.5 文档字符串 (Docstrings)

- **风格**：统一使用 **Google Style**。
- **覆盖范围**：所有模块、public 类、public 方法必须包含 Docstring。
- **内容**：必须包含简述、参数说明 (`Args`)、返回值说明 (`Returns`) 和 抛出异常说明 (`Raises`)。

### 2.6 现代 Python 习语 (Idioms & Best Practices)

- **字符串格式化**：必须优先使用 **f-strings** (`f"{var}"`)，禁止使用 `%` 格式化或 `.format()`（除非为了向后兼容极老版本）。
- **真值判断**：
    *   使用 `if my_list:` 而非 `if len(my_list) > 0:`。
    *   使用 `if value is not None:` 而非 `if value:` (防止 `0` 或 `False` 被误判)。
- **异常处理**：
    *   严禁使用裸露的 `except:`，必须捕获具体异常 `except ValueError:`。
    *   严禁在 `except` 块中使用 `pass` 且不记录日志。
- **推导式**：简单逻辑推荐使用列表/字典推导式，但如果超过两行或逻辑复杂，必须改写为 `for` 循环以保证可读性。

### 2.7 日志打印规范 (Logging Standards)

- **禁止使用 print**: 严禁在生产代码中使用 `print()`，必须使用标准库 `logging` 或 `structlog`。
- **结构化日志**: DEGUG模式按照美观文本输出，PRODUCTION模式输出 **JSON 格式**日志。默认为DEBUG模式，仅当main函数中带参数`--product`
- **日志打印粒度**: 日志的打印至少到函数粒度，每个主要函数开始和结束时候打印日志，能够在程序运行时候知道程序运行的进度。
- **日志等级定义**:
    *   `DEBUG`: 详细的调试信息（如：API 原始响应 payload，仅在开发环境开启）。
    *   `INFO`: 关键流程节点（如：`Started fetching RSS source`, `Successfully synced to Feishu`）。
    *   `WARNING`: 预期内的非致命错误（如：`Video unavailable, skipping`, `Rate limit hit, retrying in 10s`）。
    *   `ERROR`: 导致任务失败的错误（如：`Database connection failed`, `LLM API timeout`）。必须包含堆栈信息 (`exc_info=True`)。
- **日志内容要求**: 每条日志必须包含足够的上下文 (Context)：
    *   **必需字段**: `timestamp`, `level`, `module`, `message`.
    *   **上下文ID**: 在处理单条资讯时，生成一个 `trace_id` 或 `article_url` 并贯穿全流程，以便追踪该文章处理链路。
    *   **数据脱敏**: **严禁**打印 API Key、Secret、以及用户隐私信息。

## 3. 项目文件结构

```
Move37Papers/
├── spec/                   # 项目spec文件
│   ├── memory/
│   │   └── constitution.md         ## spec宪法
│   └── spec1/
│       ├── specification.md        ## 功能1的specification
│       ├── plan.md                 ## 功能1的plan
│       ├── task1.md                ## 功能1的任务1
│       └── task2.md                ## 功能1的任务2
├── src/                     # 【核心】源代码目录
│   ├── sources/                # 数据Ingest的源
│   │   ├── rss.opml                # rss源
│   │   └── youtube.yaml            # 子模块
│   ├── move37/                 # 包名 (import my_package)
│   │   ├── __init__.py             # 暴露包接口
│   │   ├── main.py                 # 入口点
│   │   ├── utils/                  # 工具函数
│   │   └── sub_module/             # 子模块
│   │       ├── __init__.py
│   │       └── core.py
│   └── samples/                # 样例代码用于验证结果是否正确
│       ├── __init__.py
│       └── sub_module/         # 子模块
│           └── sample_task1.py # 样例文件
├── deploy/                     # 部署文件目录
│   ├── entrypoint.sh           ## Docker启动后入口文件
│   └── docker-compose.yaml     ## 启动docker的docker-compose文件
├── README.md                   # 项目信息简介
├── requirements.txt            # 依赖列表 (用于复现环境)
└── .env                        # 存放URL、API Key密钥等配置信息
```

**Version**: 1.0.0 | **Ratified**: 2026-02-14 | **Last Amended**: 2026-02-14