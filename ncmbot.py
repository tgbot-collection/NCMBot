#!/usr/local/bin/python3
# coding: utf-8

# NCMBot - bot.py
# 10/26/20 20:01
#

__author__ = "Benny <benny.think@gmail.com>"

import logging
import os
import pathlib
import tempfile
import traceback
import typing

import fakeredis
import filetype
from ncmdump import dump
from pyrogram import Client, filters, types
from tgbot_ping import get_runtime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(filename)s [%(levelname)s]: %(message)s')


def customize_logger(logger: "list"):
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(filename)s [%(levelname)s]: %(message)s')
    for log in logger:
        logging.getLogger(log).setLevel(level=logging.WARNING)


def create_app(session="ytdl", workers=20):
    app_id = int(os.getenv("APP_ID", 0))
    app_hash = os.getenv("APP_HASH")
    token = os.getenv("TOKEN")

    _app = Client(session, app_id, app_hash,
                  bot_token=token, workers=workers)

    return _app


customize_logger(["pyrogram.client", "pyrogram.session.session", "pyrogram.client", "pyrogram.connection.connection"])
app = create_app()
r = fakeredis.FakeStrictRedis()
EXPIRE = 5


def edit_text(bot_msg, text):
    key = f"{bot_msg.chat.id}-{bot_msg.message_id}"
    # if the key exists, we shouldn't send edit message
    if not r.exists(key):
        r.set(key, "ok", ex=EXPIRE)
        bot_msg.edit_text(text)


def download_hook(current, total, bot_msg):
    filesize = sizeof_fmt(total)
    text = f'[{filesize}]: 下载中 {round(current / total * 100, 2)}% - {current}/{total}'
    edit_text(bot_msg, text)


def upload_hook(current, total, bot_msg):
    filesize = sizeof_fmt(total)
    text = f'[{filesize}]: 上传中 {round(current / total * 100, 2)}% - {current}/{total}'
    edit_text(bot_msg, text)


def sizeof_fmt(num: int, suffix='B'):
    for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)


def ncm_converter(tmp_name: "str", normal_name="test.ncm") -> "dict":
    # normal_name hello.ncm
    normal_name = normal_name.replace(".ncm", "")
    tmp_new_name = f"{tmp_name}.temp"
    logging.info("Converting %s -> %s", tmp_name, tmp_new_name)
    status = {"status": False, "filepath": None, "message": None}
    try:
        dump(tmp_name, tmp_new_name, False)
        ext = filetype.guess_extension(tmp_new_name)
        real_name = pathlib.PosixPath(tmp_name).parent.joinpath(f"{normal_name}.{ext}").as_posix()
        os.rename(tmp_new_name, real_name)
        status["status"] = True
        status["filepath"] = real_name
        logging.info("real filename is %s", real_name)
    except Exception:
        err = traceback.format_exc()
        logging.error("Convert failed for %s -> %s \n%s\n", tmp_name, tmp_new_name, err)
        status["error"] = err
    finally:
        return status


@app.on_message(filters.command(["start"]))
def start_handler(client: "Client", message: "types.Message"):
    chat_id = message.chat.id
    client.send_chat_action(chat_id, "typing")

    client.send_message(message.chat.id, "我可以帮你转换网易云音乐的ncm为普通的mp3/flac文件。"
                                         "直接把ncm文件发给我就可以了。"
                                         "发送完成之后请耐心等待，如果长时间没回复可以再发一次")


@app.on_message(filters.command(["about"]))
def help_handler(client: "Client", message: "types.Message"):
    chat_id = message.chat.id
    client.send_chat_action(chat_id, "typing")
    client.send_message(chat_id, "网易云ncm格式转换机器人 @BennyThink "
                                 "GitHub: https://github.com/tgbot-collection/NCMBot")


@app.on_message(filters.command(["ping"]))
def ping_handler(client: "Client", message: "types.Message"):
    chat_id = message.chat.id
    client.send_chat_action(chat_id, "typing")
    if os.uname().sysname == "Darwin":
        bot_info = "test"
    else:
        bot_info = get_runtime("botsrunner_ncmbot_1", "NCM Bot")
    client.send_message(chat_id, f"{bot_info}")


@app.on_message(filters.incoming & filters.document)
def convert_handler(client: "Client", message: "types.Message"):
    chat_id = message.chat.id
    client.send_chat_action(chat_id, "typing")
    ncm_name = message.document.file_name
    if not ncm_name.endswith(".ncm"):
        message.reply("不是ncm文件🤔", quote=True)
        return

    bot_message: typing.Union["types.Message", "typing.Any"] = message.reply("文件已收到，正在处理中……", quote=True)

    with tempfile.NamedTemporaryFile() as tmp:
        client.send_chat_action(chat_id, "typing")
        filename = tmp.name
        message.download(filename, progress=download_hook, progress_args=(bot_message,))
        bot_message.edit_text("⏳ 正在转换格式……")
        result = ncm_converter(filename, ncm_name)
        if result["status"]:
            client.send_chat_action(chat_id, "upload_audio")
            client.send_audio(chat_id, result["filepath"],
                              progress=upload_hook, progress_args=(bot_message,))
            bot_message.edit_text("转换成功!✅")
        else:
            bot_message.edit_text(f"❌转换失败\n\n{result['error'][:4000]}")


if __name__ == '__main__':
    app.run()
