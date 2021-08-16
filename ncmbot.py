#!/usr/local/bin/python3
# coding: utf-8

# NCMBot - bot.py
# 10/26/20 20:01
#

__author__ = "Benny <benny.think@gmail.com>"

import tempfile
import os
import platform
import logging
import traceback

import fakeredis
import filetype
from telethon import TelegramClient, events, utils, types
from tgbot_ping import get_runtime
from ncmdump import dump

from FastTelethon import download_file, upload_file

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(filename)s [%(levelname)s]: %(message)s')

app_id = int(os.getenv("APP_ID", 0))
app_hash = os.getenv("APP_HASH")
bot = TelegramClient('bot', app_id, app_hash,
                     device_model=f"{platform.system()} {platform.node()}-{os.path.basename(__file__)}",
                     system_version=platform.platform()
                     ).start(bot_token=os.getenv("TOKEN"))

r = fakeredis.FakeStrictRedis()
EXPIRE = 5


def sizeof_fmt(num: int, suffix='B'):
    for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)


async def download_callback(current, total, chat_id, message):
    key = f"{chat_id}-{message.id}"
    # if the key exists, we shouldn't send edit message
    if not r.exists(key):
        r.set(key, "ok", ex=EXPIRE)
        filesize = sizeof_fmt(total)
        msg = f'[{filesize}]: 下载中 {round(current / total * 100, 2)}% - {current}/{total}'
        logging.info(msg)
        new_message = f"{message.text} {msg}"
        await bot.edit_message(chat_id, message, new_message)


async def upload_callback(current, total, chat_id, message):
    key = f"{chat_id}-{message.id}"
    # if the key exists, we shouldn't send edit message
    if not r.exists(key):
        r.set(key, "ok", ex=EXPIRE)
        filesize = sizeof_fmt(total)
        msg = f'[{filesize}]: 上传中 {round(current / total * 100, 2)}% - {current}/{total}'
        logging.info(msg)
        new_message = f"{message.text} {msg}"
        await bot.edit_message(chat_id, message, new_message)


def ncm_converter(ncm_path, file_wo_ext) -> dict:
    logging.info("Converting %s -> %s", ncm_path, file_wo_ext)
    status = {"status": False, "filepath": None, "message": None}
    try:
        dump(ncm_path, file_wo_ext, False)
        ext = filetype.guess_extension(file_wo_ext)
        real_name = file_wo_ext + f".{ext}"
        os.rename(file_wo_ext, real_name)
        status["status"] = True
        status["filepath"] = real_name
        logging.info("real filename is %s", real_name)
    except Exception:
        err = traceback.format_exc()
        logging.error("Convert failed for %s -> %s \n%s\n", ncm_path, file_wo_ext, err)
        status["message"] = err
    finally:
        return status


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
        await event.reply("不是ncm文件🤔")
        return

    message = await event.reply("文件已收到，正在处理中……")

    temp_dir = tempfile.TemporaryDirectory()
    file_wo_ext = os.path.join(temp_dir.name, ncm_name[0:-4])

    with tempfile.NamedTemporaryFile() as tmp:
        async with bot.action(event.chat_id, 'audio'):
            with open(tmp.name, "wb") as out:
                await download_file(event.client, event.document, out,
                                    progress_callback=lambda x, y: download_callback(x, y, chat_id, message))
            await bot.edit_message(chat_id, message, '⏳ 正在转换格式……')
            result = ncm_converter(out.name, file_wo_ext)
        if result["status"] is False:
            async with bot.action(event.chat_id, 'typing'):
                await bot.edit_message(chat_id, message, f"{ncm_name} 转换失败❌：\n```{result}```",
                                       parse_mode='markdown')
        else:
            real_file = result["filepath"]
            async with bot.action(event.chat_id, 'document'):
                with open(real_file, "rb") as out:
                    res = await upload_file(bot, out,
                                            progress_callback=lambda x, y: upload_callback(x, y, chat_id, message))
                attributes, mime_type = utils.get_attributes(real_file)
                media = types.InputMediaUploadedDocument(
                    file=res,
                    mime_type=mime_type,
                    attributes=attributes,
                    # not needed for most files, thumb=thumb,
                    force_file=False
                )
                await bot.send_file(chat_id, media)
                await bot.edit_message(chat_id, message, '转换成功!✅')
    temp_dir.cleanup()


if __name__ == '__main__':
    bot.run_until_disconnected()
