# 信息推送飞书聊天群

## 1. 目标

### 目标1

对summarize步骤中`summarize_all`返回的results的结果进行统计，并按照如下格式，由飞书机器人应用推送消息给飞书群。

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
    * 处理结果，成功/失败，（如失败则在内容概括中写入失败原因）
- <文章2标题>
......
```

## 2. 处理方法

拼接如下的Prompt后，直接调用LLM获取返回结果。

```
你是一个AI咨询专家，对我提供的链接进行总结和分析后，使用中文给我生成这个链接的简介和深入总结，帮助我理解链接中的文章或者视频信息。具体包括：
1. 100字以内的简介，能够让我直观一眼理解文章或视频的主题内容
2. 1000字以内的文章深度介绍，如果我对这篇文章感兴趣，通过阅读这1000字以内的文字内容能够理解文章或视频的主要思想、具体的亮点。
链接如下：<链接地址，如https://www.youtube.com/watch?v=rWUWfj_PqmM>
```

## 3. Sample

一个`collect_all`函数返回的json内容样例如下
```json
{
  "collection_date": "2026-02-18",
  "target_date": "2026-02-14",
  "results": [
    {
      "source_type": "YouTube Channels",
      "source_title": "Y Combinator",
      "success": true,
      "items": [
        {
          "title": "The New Way To Build A Startup",
          "url": "https://www.youtube.com/watch?v=rWUWfj_PqmM",
          "published": "2026-02-14T15:01:34Z"
        }
      ]
    },
    {
      "source_type": "Blogs",
      "source_title": "simonwillison.net",
      "success": true,
      "items": [
        {
          "title": "Quoting Boris Cherny",
          "url": "https://simonwillison.net/2026/Feb/14/boris/#atom-everything",
          "published": "2026-02-14T23:59:09Z"
        },
        {
          "title": "Quoting Thoughtworks",
          "url": "https://simonwillison.net/2026/Feb/14/thoughtworks/#atom-everything",
          "published": "2026-02-14T04:54:41Z"
        }
      ]
    }
  ]
}
```

返回的结果如下，增加了`处理时间`、`使用模型`、`消耗token`、`简介`、`概要`几个参数
```json
{
  "collection_date": "2026-02-18",
  "target_date": "2026-02-14",
  "results": [
    {
      "source_type": "YouTube Channels",
      "source_title": "Y Combinator",
      "success": true,
      "items": [
        {
          "title": "The New Way To Build A Startup",
          "url": "https://www.youtube.com/watch?v=rWUWfj_PqmM",
          "published": "2026-02-14T15:01:34Z",
          "processing_time": "2.3s",
          "model_used": "gpt-3.5-turbo",
          "tokens_consumed": 1050,
          "brief": "本视频介绍了构建初创公司的新方法，探讨创新创业趋势与实践。",
          "summary": "本视频来自Y Combinator，深入分享了构建初创公司的最新方法和理念。演讲者围绕团队搭建、产品验证、融资策略以及如何应对创业过程中的挑战进行了细致讲解。视频里还提到实际案例，帮助观众理解理论与实操的结合。对于关注科技创业的观众来说，本视频提供了清晰的路线图和实用建议，有助于提升对初创企业发展的理解和把控。"
        }
      ]
    },
    {
      "source_type": "Blogs",
      "source_title": "simonwillison.net",
      "success": true,
      "items": [
        {
          "title": "Quoting Boris Cherny",
          "url": "https://simonwillison.net/2026/Feb/14/boris/#atom-everything",
          "published": "2026-02-14T23:59:09Z",
          "processing_time": "1.7s",
          "model_used": "gpt-3.5-turbo",
          "tokens_consumed": 860,
          "brief": "文章摘录Boris Cherny关于软件工程的洞见，简明扼要。",
          "summary": "本文主要引用了Boris Cherny关于软件工程与团队协作的见解，强调高效沟通、自动化工具的重要性，以及个人成长和团队共同进步。通过引用与分析，作者探讨如何将理论应用到实际工作流程中，帮助读者提升工程能力和组织效率。"
        },
        {
          "title": "Quoting Thoughtworks",
          "url": "https://simonwillison.net/2026/Feb/14/thoughtworks/#atom-everything",
          "published": "2026-02-14T04:54:41Z",
          "processing_time": "1.9s",
          "model_used": "gpt-3.5-turbo",
          "tokens_consumed": 910,
          "brief": "摘录Thoughtworks对于技术趋势与创新的观点，内容精炼。",
          "summary": "本文通过引用Thoughtworks的内容，对当前技术趋势、创新实践及前沿工具进行了总结。作者梳理了新兴技术如何影响开发流程和企业决策，同时探讨行业思考方式的变化。文章适合希望了解前沿IT动态的读者，具有一定参考价值。"
        }
      ]
    }
  ]
}
```
