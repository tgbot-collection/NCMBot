#!/usr/local/bin/python3
# coding: utf-8

# NCMBot - config.py
# 10/26/20 20:02
#

__author__ = "Benny <benny.think@gmail.com>"

import os

token = os.environ.get("TOKEN") or ""
# notice: this two are integers, not string
bot_id = int(os.environ.get("BOT_ID")) or 1234
client_id = int(os.environ.get("CLIENT_ID")) or 1234

api_id = os.environ.get("API_ID") or 444
api_hash = os.environ.get("API_HASH") or '123'
