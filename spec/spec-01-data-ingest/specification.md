# 数据采集的规格说明

## 1. 目标

从`src\move37\sources\rss.opml`中提取不同类型的链接，按照如下步骤操作：

- 如果链接对应sourceType为`Blogs`，则获取rss中前一天的网页链接
- 如果链接对应sourceType为`Youtube Channels`，则获取该频道指定日期发布的Youtube视频链接