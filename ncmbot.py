#!/usr/local/bin/python3
# coding: utf-8

# NCMBot - bot.py
# 10/26/20 20:01
#

__author__ = "Benny <benny.think@gmail.com>"

import tempfile
import os
import platform

from telethon import TelegramClient, events
from tgbot_ping import get_runtime

from helper import *

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(filename)s [%(levelname)s]: %(message)s')

bot = TelegramClient('bot', 1234, "api_hash",
                     device_model=f"{platform.system()} {platform.node()}-{os.path.basename(__file__)}",
                     system_version=platform.platform()
                     ).start(bot_token=os.getenv("TOKEN"))


@bot.on(events.NewMessage(pattern='/start'))
async def send_welcome(event):
    async with bot.action(event.chat_id, 'typing'):
        await bot.send_message(event.chat_id, "我可以帮你转换网易云音乐的ncm为普通的mp3/flac文件。"
                                              "直接把ncm文件发给我就可以了。"
                                              "发送完成之后请耐心等待，如果长时间没回复可以再发一次")
        raise events.StopPropagation


@bot.on(events.NewMessage(pattern='/ping'))
async def send_welcome(event):
    async with bot.action(event.chat_id, 'typing'):
        bot_info = get_runtime("botsrunner_ncmbot_1", "NCM Bot")
        await bot.send_message(event.chat_id, f"{bot_info}\n", parse_mode='md')
        raise events.StopPropagation


@bot.on(events.NewMessage(pattern='/about'))
async def send_welcome(event):
    async with bot.action(event.chat_id, 'typing'):
        await bot.send_message(event.chat_id, "网易云ncm格式转换机器人 @BennyThink "
                                              "GitHub: https://github.com/tgbot-collection/NCMBot")
        raise events.StopPropagation


@bot.on(events.NewMessage(incoming=True, func=lambda e: e.message.file))
async def echo_all(event):
    chat_id = event.message.chat_id
    ncm_name = event.message.file.name

    if event.message.file.ext != ".ncm":
        await event.reply("不是ncm文件……")
        return

    message = await event.reply("文件已收到，正在处理中……")

    temp_dir = tempfile.TemporaryDirectory()
    mp3_filepath = os.path.join(temp_dir.name, ncm_name[0:-4] + ".mp3")

    with tempfile.NamedTemporaryFile() as tmp:
        async with bot.action(event.chat_id, 'audio'):
            path = await bot.download_media(event.message, tmp.name, progress_callback=download_callback)
            result = ncm_converter(path, mp3_filepath)
        if result:
            async with bot.action(event.chat_id, 'typing'):
                await bot.edit_message(chat_id, message, f"{ncm_name} 转换失败❌：\n```{result}```",
                                       parse_mode='markdown')
        else:
            async with bot.action(event.chat_id, 'document'):
                await bot.send_file(chat_id, mp3_filepath, progress_callback=upload_callback)
                await bot.edit_message(chat_id, message, '转换成功!✅')
    temp_dir.cleanup()


if __name__ == '__main__':
    bot.run_until_disconnected()
