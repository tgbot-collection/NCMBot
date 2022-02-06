#!/usr/local/bin/python3
# coding: utf-8

# NCMBot - bot.py
# 10/26/20 20:01
#

__author__ = "Benny <benny.think@gmail.com>"

import logging
import os
import pathlib
import random
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


def ncm_converter(ncm_path: "str") -> "dict":
    ncm = pathlib.Path(ncm_path)
    tmp_name = ncm.with_suffix(".temp")
    logging.info("Converting %s -> %s", ncm_path, tmp_name)
    status = {"status": False, "filepath": None, "message": None}
    try:
        dump(ncm_path, tmp_name, False)
        ext = filetype.guess_extension(tmp_name)
        real_name = tmp_name.rename(ncm.with_suffix(f".{ext}"))
        status["status"] = True
        status["filepath"] = real_name
        logging.info("real filename is %s", real_name)
    except Exception:
        err = traceback.format_exc()
        logging.error("Convert failed for %s -> %s \n%s\n", ncm_path, tmp_name, err)
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
    logging.info("New conversion request from %s[%s]", chat_id, ncm_name)
    with tempfile.TemporaryDirectory() as tmp:
        client.send_chat_action(chat_id, "typing")
        filename = pathlib.Path(tmp).joinpath(ncm_name).as_posix()
        message.download(filename, progress=download_hook, progress_args=(bot_message,))
        bot_message.edit_text("⏳ 正在转换格式……")
        result = ncm_converter(filename)
        if result["status"]:
            client.send_chat_action(chat_id, "upload_audio")
            client.send_audio(chat_id, result["filepath"],
                              progress=upload_hook, progress_args=(bot_message,))
            bot_message.edit_text("转换成功!✅")
        else:
            bot_message.edit_text(f"❌转换失败\n\n{result['error'][:4000]}")


@app.on_message(filters.incoming)
def text_handler(client: "Client", message: "types.Message"):
    message.reply_chat_action("typing")
    text = ["世上没有什么事情比必然与偶然更难懂了，就像要懂得木头人的爱恋之情一样困难。",
            "咱活到现在，只要是让咱感到羞耻的人，咱都可以说出那个人的名字。这些名字当中还得再加上一个新的名字，那就是汝！",
            "半吊子的聪明只会招来死亡。",
            "人呐……在这种时候似乎会说『最近的年轻人……』呗。",
            "真是的，汝惊慌失措时的样子还比较可爱呐。",
            "因为汝是个大笨驴，如果没说出来，汝根本察觉不到呗。",
            "在汝的脆弱心灵冻僵前，咱得赶紧用爪子好好抓上几道伤口才行。",
            "汝不懂也罢。不……如果连汝也发现了，咱或许会有些困扰呗。",
            "哼。俗话说一不做二不休，到时候咱也会很快地把汝吃进肚子里。",
            "因为汝这种人说谎不眨眼的啊。一定会有的没的乱写一通。",
            "汝认为所有人都要遵循汝的常识是吗？",
            "说谎的时候，重点不在于说谎的内容，而在于为何要说谎。",
            "就算是咱，也有不能回答的事。",
            "汝的脑筋虽然转得快，但经验还是不够。",
            "就算如此，咱还是希望听到汝说出口。所以，重来一次。",
            "又没有人起床，也只能睡觉呗。不睡觉只会觉得冷，而且还会饿肚子。"]

    message.reply(random.choice(text))


if __name__ == '__main__':
    app.run()
