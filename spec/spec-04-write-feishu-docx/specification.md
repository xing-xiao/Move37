# 一、写入飞书知识库文档（基础模块）

## 1 创建Client类并获取token

### 1.1 目标

基于 `lark-oapi` Python SDK，先完成飞书 API 底层鉴权能力：自建应用获取 `tenant_access_token`。

飞书相关变量放在 `.env` 中：

- `FEISHU_APP_ID`：飞书应用 ID
- `FEISHU_APP_SECRET`：飞书应用密钥
- `FEISHU_CHAT_RECEIVE_ID`：飞书群接收 ID
- `FEISHU_CHAT_RECEIVE_ID_TYPE=chat_id`
- `FEISHU_WIKI_SPACE_ID`：飞书知识库 Space ID
- `FEISHU_WIKI_PARENT_NODE_TOKEN`：飞书知识库父节点 Token

### 1.2 代码结构

- `src/move37/utils/feishu/__init__.py`
- `src/move37/utils/feishu/feishuclient.py`

### 1.3 实现任务

- [x] 在 `src/move37/utils/` 下创建 `feishu` 模块目录
- [x] 在 `src/move37/utils/feishu/feishuclient.py` 中实现 `FeishuClient` 类并完成初始化
- [x] 在 `FeishuClient` 中实现 `get_tenant_access_token()` 方法，调用：
  - `POST https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal`
  - 请求体：`app_id`、`app_secret`
- [x] 对以下场景给出明确异常：
  - `app_id` 或 `app_secret` 为空
  - SDK 未安装
  - 飞书接口返回失败（HTTP/业务错误码/缺少 token）
- [x] 在类的`__init__()`方法中增加`tenant_access_token`的对象，默认为空

### 1.4 验收标准

- 调用 `FeishuClient(app_id, app_secret).get_tenant_access_token()` 时，成功返回非空 token 字符串
- 接口 `code != 0` 或无 `tenant_access_token` 时抛出异常
- 模块可被其他业务模块复用（例如后续 wiki/docx 写入流程）

### 1.5 接口说明（摘要）

- URL：`https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal`
- Method：`POST`
- Content-Type：`application/json; charset=utf-8`
- 成功返回字段：`code=0`、`tenant_access_token`、`expire`

## 2 查询飞书租户认证信息

### 2.1 目标

基于已获得的 `tenant_access_token`，通过飞书 OpenAPI 查询当前租户的认证信息，确保租户主体信息获取能力，为后续业务校验和接入打基础。

### 2.2 接口规格

- 请求方式：GET
- URL：`https://open.feishu.cn/open-apis/verification/v1/verification`
- 鉴权方式：请求头中携带 `Authorization: Bearer <tenant_access_token>`

### 2.3 关键字段

- `status`：认证状态
- `type`：主体类型（企业/团队等）
- `tenant_name`：租户名称
- `certification_url`：认证详情页链接
- 其它租户主体信息

### 2.4 主要任务

- [ ] 设计 `get_tenant_verification_info()` 方法，要求：
  - 内部调用上述接口，自动附加 token
  - 接口错误码/无效 token/请求失败等需抛出明确异常
  - 成功时，返回结构化认证信息字典
- [ ] 在 `feishuclient.py` 中补充该方法，并完善错误处理

### 2.5 验收标准

- 在`src\samples\feishu\`目录下创建`tenant_verification.py`，作为测试main函数入口
- 可直接基于已获取的 tenant_access_token 查询租户认证信息
- 认证信息字段完整、数据结构规范
- 错误场景均有清晰报错提示


## 3 创建wiki文档（DOCX节点）

### 3.1 目标

- 实现 `create_docx` 方法，基于飞书 OpenAPI 创建一个新的 Wiki 文档（DOCX 类型节点）。
- 支持自定义文档标题、内容和父节点位置，并返回新创建文档的详细信息。

### 3.2 接口规格

- [Wiki空间节点-创建接口文档](https://open.feishu.cn/document/server-docs/docs/wiki-v2/space-node/create)
- 请求方式：POST
- URL：`https://open.feishu.cn/open-apis/wiki/v2/space-node/create`
- 鉴权方式：请求头携带 `Authorization: Bearer <tenant_access_token>`
- Content-Type: `application/json; charset=utf-8`
- 主要请求参数：
  - `space_id`（string）：Wiki空间ID，必填
  - `parent_node_token`（string）：父节点token，支持创建于根目录或指定目录下，必填
  - `obj_type`（string）：对象类型，文档为"docx"，默认为"docx"
  - `node_name`（string）：文档标题，默认为"origin"
  - `title`（string）：文档标题，限制不超过500个字符，必填
- 主要响应字段：
  - `node_token`：新建节点token
  - `obj_token`：新建文档token
  - `wiki_node_url`：新Docx页面的URL
  - 其它节点/文档信息

### 3.3 主要任务

- [ ] 设计并实现 `create_docx(space_id, node_name, parent_node_token=None, title=None, ...):` 方法（或类方法），主要要求：
  - 自动携带 tenant_access_token 完成接口请求
  - 支持自定义标题与父节点
  - 需健壮处理接口错误/鉴权异常，出现 code!=0、无返回对象等时抛出明确异常
  - 返回结构化字典，包含创建成功的 docx 节点的所有关键信息
- [ ] 在 `feishuclient.py` 中实现，接口签名参数尽量贴合飞书OpenAPI规范

### 3.4 验收标准

- - 在`src\samples\feishu\`目录下创建`create_doc.py`，作为测试main函数入口
- 能正确基于实际空间ID和Token创建Docx文档，接口返回包含节点token、文档token和可访问的url
- 文档内容可正确写入，页面可在浏览器打开
- 错误情况（权限不足、ID错误、token失效等）均有清晰报错提示

## 4 向 Wiki 文档写入内容

### 4.1 目标

- 实现为已存在的 Feishu Wiki Docx 节点插入或更新正文内容的自动化能力
- 支持基础富文本结构体，如：标题（heading）、正文段落（paragraph）、加粗（bold）、引用块（quote）等常用格式
- 能通过接口写入（追加）内容到指定 Docx 文档，并能够通过浏览器/接口实时看到同步结果

### 4.2 接口规格

- [文档内容-创嵌套建块（Blocks 批量插入）](https://open.feishu.cn/document/docs/docs/document-block/create-2)
- 请求方式：POST
- URL：`https://open.feishu.cn/open-apis/docx/v1/documents/:document_id/blocks/:block_id/descendant`
- 鉴权方式：请求头需携带 `Authorization: Bearer <tenant_access_token>`
- Content-Type：`application/json; charset=utf-8`
- 主要参数说明：
  - `document_id`（string）：目标 Docx 文档ID，取自Wiki创建接口返回的"obj_token"，必填
  - `block_id`（string）：父块ID，通常为文档根块，可直接用创建接口的"node_token"，必填
  - `children`（list）：要插入的块内容，结构和格式参考飞书文档Block定义（支持多种类型组合）
    - 块类型举例：`heading1`、`paragraph`、`quote`，每种块的内容格式详见[官方文档](https://open.feishu.cn/document/server-docs/docs/element/block/overview)

### 4.3 主要任务

- [ ] 实现 `write_docx_content(document_id, block_id, children, ...)` 方法（或等价类方法）
  - 自动集成 tenant_access_token 完成接口鉴权
  - 支持多种常用块类型，并保证插入内容结构规范
  - 出现接口错误、鉴权异常及响应 code!=0 时需抛出明确异常
  - 返回插入后的块信息（block_id 等），并能用以后续内容追加
- [ ] 方法建议实现于 `feishuclient.py`，参数约束及顺序尽量贴合飞书OpenAPI文档

### 4.4 验收标准

- 在`src\samples\feishu\`目录下创建`write_docx.py`，提供主要测试入口
- 能基于有效 token 正确向指定 Docx 文档写入/追加所需格式的内容块（如标题、正文、引用等富文本块）
- 页面可在浏览器实时刷新查看内容写入效果
- 各类失败场景（鉴权失效、参数非法、文档/块ID错误等）均有清晰的异常提示

## 5. 基于 summary 结果自动生成 Wiki 文档

### 5.1 目标

- 根据 content-summarize 的 summary_result 结构，自动在指定飞书 Knowledge Base (Wiki/Docx) 中组织创建与同步内容
- 持续、可复用地生成符合团队查阅需求的文档分层，涵盖每日主文档、各来源子文档，以及针对博客的翻译、公众号内容

### 5.2 流程及关键功能

1. **主文档创建/获取**

   - 以 `target_date` 作为标题（如“2026-02-14咨询摘要”）在指定 Wiki 空间下创建主 Docx 文档（若已存在则复用）
   - 主文档包含当前所有资讯源分组（如各博客、各 YouTube 频道）

2. **分组内容节点生成**

   - 对 `summary_result["results"]` 中每一来源（如博客、YouTube Channels）：
     - 在主文档下按来源类型及名称依次创建子节点（如“Y Combinator”, “simonwillison.net”）
     - 每个来源节点下，遍历其 items 列表，针对每篇文章/视频，生成独立的内容子块

3. **内容块详细写入**

   - 对每条 item，生成包含以下内容的富文本块（推荐按如下顺序展现）：
     - 标题（heading1 或 heading2，内容为 item["title"]）
     - 基本元数据（如 url、published、model_used、tokens_consumed、processing_time，可表格或段落呈现）
     - `brief` 字段（如有，内容放于一级引用块 quote）
     - `summary` 字段（正文段落插入）
   - 若来源类型为“Blogs”，进一步调用翻译与公众号稿生成接口，将结果作为独立子节点或附录插入，下方标签标记（如“[自动翻译]”、“[微信公众号]”）

4. **块追加逻辑**

   - 支持追加内容到同文档/同节点，实现多日多内容可迭代维护
   - 返回所有已写入文档的 block_id/token 信息，便于后续追加

5. **异常与日志处理**

   - 所有飞书接口错误、权限问题需显式捕获、详细报错
   - 操作日志支持详细跟踪每一步文档创建与内容写入，便于排查及任务回溯

### 5.3 接口建议

- 推荐以 `FeishuWikiWriter.write_summary_to_wiki(summary_result, space_id, parent_node_id, ...)` 为主要 API
- 支持 dry-run 及 debug 模式（不实际推送，仅组织待同步内容供预览）
- 支持自定义空间（space_id）、父节点、文档标题模板等

### 5.4 验收标准

- 实际调用 summary_result 样例数据，能在实际 Wiki 空间自动生成结构化文档
- 页面内容符合分层、富文本、附加翻译/公众号内容等展示要求
- 所有失败、异常场景有明确错误提示