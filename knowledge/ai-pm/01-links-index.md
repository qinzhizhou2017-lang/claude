# 链接全索引

> 归档日期：2026-07-03。「已验证」指通过搜索引擎确认存在并与本知识库直接相关。

## 一、主链接（用户提供）

| # | 链接 | 说明 | 状态 |
|---|---|---|---|
| 1 | https://www.feishu.cn/community/article?id=7444818740039909395 | 飞书社区文章《Mark的AI产品经理知识库「持续更新」》，知识库的对外介绍页 | 已验证，原文待抓取 |
| 2 | https://qqs7y1hozd1.feishu.cn/wiki/DzlJw541diset0kFeYJcTlH3nRh | Mark 的飞书 Wiki 知识库页面（租户 qqs7y1hozd1，与文章同一作者体系） | 已验证存在，原文待抓取 |

## 二、已发现的同体系子链接

| 链接 | 说明 | 来源 |
|---|---|---|
| https://qqs7y1hozd1.feishu.cn/wiki/QnPwwpKgKiGpFCkUrs7ciMIbnff | 《零基础入门大语言模型底层技术原理》——面向非科班读者（含投资人）的 LLM 原理长文，覆盖 MLP→CNN→RNN/LSTM/GRU→RL→seq2seq→自监督→Transformer→GPT（IFT/SFT/RLHF/CoT）→BERT，持续更新 | 搜索快照 |
| https://www.feishu.cn/community/article?id=7577703602626497758 | 另一篇同名社区文章《Mark的AI产品经理知识库》（更新版/姊妹篇） | 搜索结果 |

## 三、镜像与转载（可作原文替代来源）

| 链接 | 内容 | 备注 |
|---|---|---|
| https://blog.csdn.net/weixin_45182273/article/details/144684195 | 《浅析多模态大模型的前世今生》 | CSDN 转载，标注出自本知识库 |
| https://blog.csdn.net/weixin_45182273/article/details/144784888 | 《三天练完，没有AI产品面试难的住你》 | CSDN 转载，标注出自本知识库 |
| https://blog.csdn.net/weixin_45182273/article/details/144878631 | 《某大厂大模型技术面经》（含"训练大模型一般要16倍参数量"等考点） | CSDN 转载 |
| https://blog.csdn.net/weixin_45182273/article/details/144662620 | 《产品经理需要懂技术吗？懂到什么程度？》 | CSDN 转载 |
| https://www.zjnav.com/22236.html | 终极导航对本知识库的收录介绍页 | 第三方介绍 |
| https://yeeach.com/443/mark%E7%9A%84ai%E4%BA%A7%E5%93%81%E7%BB%8F%E7%90%86%E7%9F%A5%E8%AF%86%E5%BA%93/ | 博客对本知识库的介绍/收藏 | 第三方介绍 |

## 四、待抓取清单（爬虫种子）

供 `tools/crawl_feishu_kb.py` 使用：

```
https://www.feishu.cn/community/article?id=7444818740039909395
https://www.feishu.cn/community/article?id=7577703602626497758
https://qqs7y1hozd1.feishu.cn/wiki/DzlJw541diset0kFeYJcTlH3nRh
https://qqs7y1hozd1.feishu.cn/wiki/QnPwwpKgKiGpFCkUrs7ciMIbnff
```

爬虫会从 Wiki 侧边栏树自动发现其余全部子页面（同一 Wiki 空间内 BFS 遍历）。
