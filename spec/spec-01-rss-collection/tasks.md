# 数据采集实现任务列表

## 1. 项目初始化
- [ ] 1.1 创建项目目录结构
  - 创建 `src/move37/utils/opml/` 目录
  - 创建 `src/move37/utils/rss/` 目录
  - 创建 `src/move37/utils/youtube/` 目录
  - 创建 `src/move37/ingest/` 目录
  - 创建 `src/samples/ingest/` 目录
  - 创建必要的 `__init__.py` 文件

- [ ] 1.2 安装项目依赖
  - 创建 `requirements.txt` 文件
  - 添加依赖: feedparser, requests, python-dateutil, lxml
  - 安装依赖包

## 2. OPML 解析模块
- [ ] 2.1 实现 OPML 解析器
  - 文件: `src/move37/utils/opml/opml_parser.py`
  - 实现 `parse_opml(file_path)` 函数
  - 解析 XML 结构，提取 `<outline>` 节点
  - 识别 `sourceType` 属性
  - 提取 `text` 和 `xmlUrl` 属性
  - INFO类型日志输出获取到的类型和个数的统计结果
  - 返回结构化列表: `[{"sourceType": "...", "xmlTitle": "...", "xmlUrl": "..."}]`

- [ ] 2.2 测试 OPML 解析器
  - 使用 `src/move37/sources/rss.opml` 测试
  - 验证能正确识别 RSS 和 YouTube 源
  - 验证输出格式正确

## 3. 日期工具模块
- [ ] 3.1 实现日期工具函数
  - 文件: `src/move37/utils/date_utils.py`
  - 实现 `get_yesterday_range()` 函数：返回前一天的开始和结束时间
  - 实现 `get_date_range(date_str)` 函数：返回指定日期的开始和结束时间
  - 实现 `parse_date(date_str)` 函数：解析日期字符串
  - 处理时区问题（使用 UTC）

- [ ] 3.2 测试日期工具函数
  - 测试前一天日期计算
  - 测试指定日期解析
  - 测试边界情况（跨月、跨年）

## 4. RSS 采集模块
- [ ] 4.1 实现 RSS 采集器
  - 文件: `src/move37/utils/rss/rss_collector.py`
  - 实现 `collect_rss(feed_url, start_time, end_time)` 函数
  - 使用 `feedparser` 解析 RSS/Atom feed
  - 筛选发布时间在指定范围内的文章
  - 提取文章标题、链接、发布时间
  - INFO类型日志输出"对<xmlTitle>(<xmlUrl>)parse完毕，共获取x个有效文章。
  - 返回文章列表

- [ ] 4.2 添加错误处理
  - 网络请求失败重试（最多 3 次）
  - Feed 解析失败处理
  - 日期解析异常处理

- [ ] 4.3 测试 RSS 采集器
  - 使用真实 RSS feed 测试（simonwillison.net）
  - 验证日期筛选逻辑
  - 测试错误处理机制

## 5. 主功能实现
- [ ] 5.1 实现数据采集协调器
  - 文件: `src/move37/ingest/collection.py`
  - 实现 `collect_all(target_date=None)` 函数
  - 解析 OPML 文件获取数据源列表
  - 遍历数据源，调用对应采集器，采集指定日期的信息
  - 汇总所有结果

- [ ] 6.2 实现结果格式化
  - 实现 `format_results(results)` 函数
  - 按照指定的 JSON 格式输出
  - 如果results中的items数量为0，则不加入json中
  - 包含 collection_date, target_date, results

- [ ] 6.3 测试主功能
  - 端到端测试完整流程
  - 验证 RSS 和 YouTube 采集都正常工作
  - 验证结果格式正确

## 7. 命令行接口
- [ ] 7.1 实现命令行入口
  - 文件: `src/samples/ingest/collection.py`
  - 实现 `main()` 函数
  - 使用 `argparse` 解析命令行参数
  - 支持 `--date` 参数指定目标日期
  - 默认使用前一天日期
  - 调用 `collect_all()` 函数
  - 打印采集结果

- [ ] 7.2 测试命令行接口
  - 测试不带参数运行（使用默认日期）
  - 测试带 `--date` 参数运行
  - 测试无效日期格式处理

## 8. 集成测试与优化
- [ ] 8.1 端到端集成测试
  - 运行完整流程，验证所有功能
  - 测试真实数据源
  - 验证输出格式

- [ ] 8.2 性能优化（可选）
  - 添加并发请求支持
  - 优化网络请求性能

- [ ] 8.3 文档完善（可选）
  - 添加代码注释
  - 编写 README 使用说明
  - 添加示例输出

## 任务优先级说明

**高优先级**（必须完成）:
- 任务 1: 项目初始化
- 任务 2: OPML 解析模块
- 任务 3: 日期工具模块
- 任务 4: RSS 采集模块
- 任务 6: 主功能实现
- 任务 7: 命令行接口

**中优先级**（重要）:
- 任务 5: YouTube 采集模块
- 任务 8.1: 集成测试

**低优先级**（可选）:
- 任务 8.2: 性能优化
- 任务 8.3: 文档完善
