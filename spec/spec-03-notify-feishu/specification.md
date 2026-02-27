# 信息推送飞书聊天群

# 一、飞书群消息推送（Bot 通知模块）

## 1.1 目标

基于 `lark-oapi` Python SDK，实现将在 summarize 步骤中 `summarize_all` 返回的 results 进行汇总统计，并以结构化富文本消息，通过飞书机器人应用自动推送到指定飞书群。

- 自动统计总处理内容数、成功/失败数、执行耗时、消耗 Token 数等指标
- 按规范格式组织消息文本（见下方格式示例）
- 群内消息支持区分条目展示失败与成功，失败项需给出失败原因

## 1.2 代码结构

- `src/move37/utils/feishu/__init__.py`
- `src/move37/utils/feishu/feishuclient.py`
- `src/move37/notify/`（通知业务层；直接调用 utils 中 `FeishuClient`）
- 示例脚本：`src/samples/notify/notify.py`

## 1.3 实现任务

- [x] 复用 `src/move37/utils/feishu/feishuclient.py` 中 `FeishuClient`，不在 `notify` 模块重复实现鉴权和底层 HTTP 调用
- [x] 在通知业务层通过 utils 封装使用 `send_group_notify(content: str, receive_id: str, msg_type: str = "interactive", ...):` 方法
  - 自动携带 tenant_access_token 鉴权
  - `content` 为生成的消息正文，支持 markdown/富文本
  - `receive_id` 为推送目标群 ID，建议从环境变量读取
  - 支持消息类型参数扩展，如 `msg_type="text"|"post"|"interactive"`
  - 接口异常、权限失败等需抛出明确异常
  - 返回消息发送结果或消息 id
- [x] 增加汇总消息内容自动拼装工具函数，将 summarize_all 结果渲染为规范文本
- [x] 错误或异常场景输出详细报错提示
- [x] 删除 `src/move37/notify/feishu_client.py`，统一由 `notify/notifier.py` 直接调用 utils FeishuClient

## 1.4 消息内容规范

消息内容示例（分区段落，支持 markdown/富文本）：

```
## 执行结果总结

- 处理文章/视频数：<x>个，成功<x>个，失败<x>个
- 执行时间：<x>分<x>秒
- 消耗Token：<x>个

## 文章清单

- <文章1标题>
    * 来源：内容为作者、频道名称
    * 原文链接：文章链接字段
    * 消耗Token：<x>个
    * 文章简介：brief内容
    * 处理结果：成功/失败（如失败则在内容概括或备注中写失败原因）
- <文章2标题>
……
```

> **说明：** 
> - 群通知消息体建议采用 `post` 或 `interactive` 类型，以支持结构化块和更好的可读性。
> - 每篇文章/视频均输出作者/频道、简介、结果及原因。
> - 消息体建议自动截断超长条目或增加总数提示。

## 1.5 接口规格

- [群消息-下发接口](https://open.feishu.cn/document/server-docs/im-v1/message/create)
- 请求方式：POST
- URL：`https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id`
- 鉴权方式：`Authorization: Bearer <tenant_access_token>`
- Content-Type：`application/json; charset=utf-8`
- 主要请求参数：
  - `receive_id`: 群聊ID，推荐从 `.env` 提取 `FEISHU_CHAT_RECEIVE_ID` 环境变量
  - `msg_type`: 支持 `text`、`post`、`interactive`，推荐 `post/interactive`
  - `content`: 结构化消息体（JSON 格式、详见官方文档）
- 主要响应字段：
  - `code`: =0 为成功
  - `data.message_id`: 消息唯一 id

## 1.6 验收标准

- 创建 `src/samples/feishu/chat_notify.py` 主入口程序
- 构造 mock 的 Summary_Result 测试数据
- 实现消息推送后，群内可直接收到格式化统计消息
- `notify` 模块复用了 `src/move37/utils/feishu/feishuclient.py`，自动注入 token 与群聊 id
- 失败场景下能输出详细错误及异常原因
- 支持功用封装，方便后续其它业务直接调用
