# AI咨询服务

## 1. 目标

将spec01到spec05各个步骤组合，生成一个AI咨询自动获取的应用，每日从rss文件的博客、Youtube内容中获取最新的咨询信息，对内容进行提取、翻译、总结后，同步到飞书文档，发送飞书群消息，并为微信公众号生成撰写文章。

具体步骤包括

- 使用rss-collection获取咨询信息
- 使用content-summarize对咨询信息进行分析总结
- 使用notify-feishu发送每日的消息
- 使用write-feishu-docx在飞书知识库生成文档

## 2. 代码

- 在`/src/move37/main.py`中作为入口代码
- 如果不输入参数则每日早上5点开始运行程序
- 输入带--direct参数直接执行
