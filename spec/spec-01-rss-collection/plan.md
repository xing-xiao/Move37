# 数据采集实现计划

## 概述
实现从 OPML 文件中提取不同类型的数据源链接，并根据`sourceType`类型获取内容：
- Blogs：获取指定日期发布的内容链接
- YouTube Channels：获取指定日期发布的视频链接

## 实现步骤

### 1. OPML 解析模块
**文件**: `src/move37/utils/opml/opml_parser.py`

**功能**:
- 解析 `src/move37/sources/rss.opml` 文件
- 提取所有 `<outline>` 节点
- 识别并分类不同类型的数据源（RSS 或 YouTube）
- 返回结构化的数据源列表

**输出格式**:
```python
[
    {"sourceType": "Blogs", "xmlTitle": "simonwillison.net", "xmlUrl": "https://simonwillison.net/atom/everything/"},
    {"sourceType": "YouTube Channels", "xmlTitle": "AI Engineer", "xmlUrl": "https://www.youtube.com/channel/UCLKPca3kwwd-B59HNr-_lvA"},
    ...
]
```

### 2. RSS 采集模块
**文件**: `src/move37/utils/rss/rss_collector.py`

**功能**:
- 接收 RSS feed URL
- 解析 RSS/Atom feed 内容
- 筛选指定日期发布的文章或视频链接
- 提取文章链接、标题、发布时间等元数据

**依赖库**: `feedparser`

**关键逻辑**:
- 使用 `feedparser` 解析 RSS/Atom feed
- 返回指定日期的文章或视频列表

### 3. 主功能实现
**文件**: `src/move37/ingest/collection.py`

**功能**:
- 协调整个数据采集流程
- 调用 OPML 解析器获取数据源列表
- 采集器采集结果
- 汇总所有采集结果
- 输出或保存结果

**流程**:
```
1. 解析 OPML 文件
2. 获取目标日期（命令行参数）
3. 遍历数据源列表
4. 调用采集器
5. 收集所有结果
6. 输出结果（JSON）
```

### 5. 主控制器
**文件**: `src/samples/ingest/collection.py`

**功能**:
- main函数调用`src/move37/ingest/collection.py`的功能函数
- 输入参数为指定日期，示例: `python samples/ingest/collection.py --date 2026-02-17`
- 输出为打印获取的链接

## 依赖项

```txt
feedparser>=6.0.0
requests>=2.31.0
python-dateutil>=2.8.0
lxml>=4.9.0
argparse  # 标准库，用于命令行参数解析
```

## 数据输出格式

```json
{
  "collection_date": "2026-02-18",
  "target_date": "2026-02-17",
  "results": [
    {
      "source_type": "Blogs",
      "source_title": "simonwillison.net",
      "success": true,
      "items": [
        {
          "title": "文章标题",
          "url": "https://example.com/article",
          "published": "2026-02-17T10:30:00Z"
        }
      ]
    },
    {
      "source_type": "YouTube Channels",
      "source_title": "AI Engineer",
      "success": true,
      "items": [
        {
          "title": "视频标题",
          "url": "https://www.youtube.com/watch?v=xxxxx",
          "published": "2026-02-17T15:00:00Z"
        }
      ]
    }
  ]
}
```

## 错误处理

- 网络请求失败：重试机制（最多 3 次）
- Feed 解析失败：记录错误日志，继续处理其他源
- 日期解析异常：使用默认时区或跳过该条目
- 空结果：正常返回空列表

## 测试计划

1. **单元测试**
   - OPML 解析器测试
   - 采集器测试（使用 mock 数据）
   - 日期工具函数测试

2. **集成测试**
   - 端到端流程测试
   - 真实数据源测试（可选）

## 实现优先级

1. **高优先级**（核心功能）
   - OPML 解析模块
   - RSS 采集模块
   - 日期工具函数
   - 主控制器基本流程

2. **低优先级**（可选）
   - 日志系统
   - 配置文件管理
   - 单元测试

## 预计工作量

- OPML 解析: 1-2 小时
- RSS 采集: 2-3 小时
- 主控制器和集成: 1-2 小时
- 测试和调试: 2-3 小时

**总计**: 8-13 小时
