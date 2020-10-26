# NCMBot
🐿️ 能够帮你把网易云音乐ncm格式转换为flac的Telegram Bot

[🐿️ NCMBot](https://t.me/netease_ncm_bot)

# 使用方法
直接发送文件给bot即可

# 截图
![](assets/1.jpeg)

# 大文件支持
由于Telegram bot仅支持下载10M文件，因此如果要支持超过10M大文件，就需要用client来解决。

需要去 [Telegram API](my.telegram.org) 申请自己的ID和hash。

# 部署
## 普通方式
```shell script
git clone https://github.com/tgbot-collection/NCMBot
cd NCMBot
# 修改 config.py，或者配置环境变量
pip3 install -r requirements.txt
python ncmbot/bot.py
python ncmbot/client.py
```
## docker

```shell script

# 切换到项目根目录,修改环境配置
vim config.env 
# 创建数据库
touch ncmbot/client.session ncmbot/bot.session
# 然后进入容器进行基础配置
docker run --rm -it -v $(pwd)/ncmbot/client.session:/NCMBot/ncmbot/client.session bennythink/ncmbot sh
# 在容器内运行如下命令
cd ncmbot
python client.py
# 然后输入手机号和验证码，登录client端，Ctrl+C退出即可
docker-compose up -d
```

# TODO
- [x] 支持大文件

# Commands
```
start - 开始使用机器人
about - 关于机器人
ping - 运行信息
```

# License
Apache License 2.0