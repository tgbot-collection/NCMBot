#!/usr/local/bin/python3
# coding: utf-8

# NCMBot - client.py
# 10/26/20 19:32
#

__author__ = "Benny <benny.think@gmail.com>"

import tempfile
from telethon import TelegramClient, events

from config import *
from helper import *

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(filename)s [%(levelname)s]: %(message)s')

client = TelegramClient('client', api_id, api_hash,
                        device_model="Benny-NCM", system_version="99.9", app_version="1.0.0")


@client.on(events.NewMessage(incoming=True, pattern='(?i).*ping.*'))
async def my_event_handler(event):
    await event.reply('pong!')
    raise events.StopPropagation


@client.on(events.NewMessage(incoming=True, forwards=True, from_users=bot_id, func=lambda e: e.message.file))
async def my_event_handler(event):
    chat_id = event.chat_id
    ncm_name = event.message.file.name
    noext_filename = ncm_name[0:-4]

    logging.info("[client] receive from %s, %s", chat_id, ncm_name)

    temp_dir = tempfile.TemporaryDirectory()
    mp3_filepath = os.path.join(temp_dir.name, ncm_name[0:-4] + ".mp3")
    with tempfile.NamedTemporaryFile() as tmp:
        async with client.action(chat_id, 'audio'):
            path = await client.download_media(event.message, tmp.name, progress_callback=download_callback)
            result = ncm_converter(path, mp3_filepath)
        if result:
            async with client.action(chat_id, 'typing'):
                await event.reply(f"{ncm_name} 转换失败❌：\n```{result}```", parse_mode='markdown')
        else:
            async with client.action(chat_id, 'document'):
                # await client.send_file(chat_id, mp3_filepath, progress_callback=upload_callback)
                await event.reply('转换成功!✅', file=mp3_filepath)
                logging.info("file send complete")
    temp_dir.cleanup()


if __name__ == '__main__':
    client.start()
    client.run_until_disconnected()
