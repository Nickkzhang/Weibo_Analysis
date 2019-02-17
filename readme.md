# 用户微博内容分析与统计
## 目的
获取用户所发布的微博，并进行统计及内容分析。
## 方式
### 01. 微博API
最理想的方式是在用户登陆后，通过新浪提供的微博API获取用户所有微博信息。但由于新浪对于API的返回数据量有限制，此法无法实现。<br>
具体见[：新浪微博开放平台](https://open.weibo.com/wiki/2/statuses/user_timeline)<br>
API操作见：UserSinaweibopy3.py文件
### 02.爬虫
01无法达到目的后，改用暴力爬虫进行微博内容的获取。<br>
最终效果：
![image](https://www.showdoc.cc/server/api/common/visitfile/sign/7d91fa098867b3ab7977750eb45ed049?showdoc=.jpg)
存在的问题：
- 需要手动获取目标用户的UID
- 需要开发者事先登陆获取cookie
- 获取的目标用户的微博数量不稳定（大部分情况下只能获取大部分，而不能每次获取全部）
- 情感分析待优化
- 表情统计待优化

## 文件说明 

Crawler
- bg.jpg 背景图片
- 华文细黑.ttf 图片上汉字的字体
- show.html 部署在服务器上时一个简易的前端界面
- weibo_analysis.py 获取并分析

API
- UserSinaweibopy3.py API使用样例
- sinaweibopy3.py API使用封装

## 服务器展示
[在线演示](http://www.digiview.tech/zdd/show.html)
