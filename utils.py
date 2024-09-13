import datetime
import json
import logging
import os
from bs4 import Tag

# 初始化日志记录器
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# SAVED_TAG = '【已缓存】'

# 初始化日志记录器
# 读取配置文件
with open("config.json", encoding='utf-8') as fp:
    CONFIG = json.load(fp)

# 从配置文件中获取配置信息
PROXY = CONFIG["proxy"]
OUTPUT_DIR = CONFIG["output"]
BASE_URL = CONFIG["host"]
SUBSCRIBTIONS_LIST = CONFIG["subscriptions"]
COOKIEFILE = CONFIG["cookiefile"]
WEBDAV = CONFIG["webdav"]
WEBDAV_HOST, WEBDAV_PATH, WEBDAV_USER, WEBDAV_PASS = WEBDAV

ydl_opts = {
    # "cookiefile": COOKIEFILE,
    "cookiesfrombrowser": ['firefox'],
    "proxy": PROXY,
    "format": "bestaudio/best",
    "postprocessors": [
        {
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }
    ],
    "outtmpl": os.path.join(OUTPUT_DIR, "%(uploader_id)s/%(id)s.%(ext)s"),
}


def sort_by_published_date(channel: Tag):
    # Extract all items and non-item elements separately
    items = []
    non_items = []
    for element in list(channel):
        if element.name == "item":
            items.append(element)
        else:
            non_items.append(element)

    # Remove all elements from the channel temporarily using extract()
    for element in items + non_items:
        element.extract()

    # Sort items by the 'pubDate' in descending order
    items.sort(key=lambda x: datetime.datetime.strptime(x.find('pubDate').text, '%a, %d %b %Y %H:%M:%S GMT'), reverse=True)

    # Reinsert non-item elements first
    for element in non_items:
        channel.append(element)

    # Then append sorted items
    for item in items:
        channel.append(item)