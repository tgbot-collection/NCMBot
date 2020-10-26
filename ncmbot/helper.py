#!/usr/local/bin/python3
# coding: utf-8

# NCMBot - helper.py
# 10/27/20 09:16
#

__author__ = "Benny <benny.think@gmail.com>"

import logging
import traceback

from ncmdump import dump

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(filename)s [%(levelname)s]: %(message)s')


def download_callback(current, total):
    logging.info('Downloaded %s out of %s, %.2f%%', current, total, current / total * 100)


def upload_callback(current, total):
    logging.info('Uploaded %s out of %s, %.2f%%', current, total, current / total * 100)


def ncm_converter(ncm_path, mp3_path):
    logging.info("Converting %s -> %s", ncm_path, mp3_path)
    try:
        dump(ncm_path, mp3_path, False)
    except Exception:
        err = traceback.format_exc()
        logging.error("Convert failed for %s -> %s \n%s\n", ncm_path, mp3_path, err)
        return err
