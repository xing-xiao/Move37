# 写入飞书知识库文档

## 1. 目标

### 目标1

将飞书机器人应用推送消息给飞书群的内容，写入飞书的知识库文档，文档的Title为"target_date"的日期。

### 目标2

对每个Item内容，按照文章的标题Title创建**目标1**生成文档的子文档，内容格式如下：

```
## 1 文章标题
    * 来源：内容为作者、频道名称
    * 原文链接：文章链接字段
    * 发布时间：xxxxx
    * 消耗Token：<x>个
    * 文章简介：brief内容
    * 处理结果，成功/失败，（如失败则在内容概括中写入失败原因）

## 2 文章总结

<summary内容>

## 3 翻译文章

提取文章内容，翻译作为子文档的链接

## 4 生成公众号文章

LLM为这篇内容生成的公众号文章，作为本文档的子文档，此处放子文档链接

```
如果是Youtube视频，则**3 翻译文章**和**4 生成公众号文章**不处理，仅对播客文章包含3、4两节

### 目标3

对博客文章，生成**目标2**文档的子文档`翻译文章`和`生成公众号文章`。

- 对于**翻译文章**：提取Blogs链接中的文章，使用LLM按照段落翻译，翻译后内容是原文在上、中文翻译在下；然后将翻译内容放置于`翻译文章`的文档中。
- 对于**生成公众号文章**：使用LLM对Blogs内容进行总结，生成一个AI咨询类公众号的文章。

* 注意，Youtube视频不进行这类操作

## 2. 接口与配置约束

### 2.1 飞书接口约束

`write-feishu-docx` 仅使用以下接口：

1. 创建 wiki 节点（文档）  
   `https://open.feishu.cn/document/server-docs/docs/wiki-v2/space-node/create`
2. 写入文档内容块  
   `https://open.feishu.cn/document/docs/docs/document-block/create-2`

### 2.2 环境变量约束

`write-feishu-docx` 除复用飞书应用鉴权配置（`FEISHU_APP_ID`、`FEISHU_APP_SECRET`）外，仅新增以下两个配置：

- `FEISHU_WIKI_SPACE_ID`：目标知识库 space id
- `FEISHU_WIKI_PARENT_NODE_TOKEN`：写入文档的父节点 token

系统应在 `FEISHU_WIKI_SPACE_ID` 指定的知识库中，以 `FEISHU_WIKI_PARENT_NODE_TOKEN` 作为父节点创建主文档和后续子文档。

## 3. 测试样例文件

- 示例脚本：`src/examples/write-feishu-docx/write-feishu-docx.py`
- 测试文件：`src/examples/write-feishu-docx/test_write_feishu_docx.py`

测试重点：

1. 固定接口地址是否与本 spec 一致
2. `FEISHU_WIKI_SPACE_ID` 和 `FEISHU_WIKI_PARENT_NODE_TOKEN` 的必填校验
3. Blogs 与 YouTube 在文档结构上的分支差异（YouTube 不包含第 3/4 节）
