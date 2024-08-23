import logging
import os
import random
import time

import bs4
import requests
from yt_dlp import YoutubeDL

from utils import PROXY

# 设置日志记录
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 配置参数
COOKIEFILE = 'path_to_cookiefile'
OUTPUT_DIR = 'downloads'
BASE_URL = '{$host_placeholder}'

ydl_opts = {
    # "cookiefile": COOKIEFILE,
    "cookiesfrombrowser": ['chrome'],
    "proxy": PROXY,
    "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
    "postprocessors": [
        {
            "key": "FFmpegVideoConvertor",
            "preferedformat": "mp4",
        }
    ],
    "outtmpl": os.path.join(OUTPUT_DIR, "%(uploader_id)s/%(id)s.%(ext)s"),
}

def save_feed(soup, xml_path):
    with open(xml_path, 'w', encoding='utf-8') as f:
        f.write(str(soup))

def download_videos(name: str, feed_url: str, requester: requests.Session, ydl_opts: dict):
    # 构建本地XML文件路径
    xml_path = os.path.join(OUTPUT_DIR, '@' + name + '.xml')
    video_xml_path = os.path.join(OUTPUT_DIR, '!' + name + '.xml')
    # 如果本地文件不存在，则从URL获取并保存
    if not os.path.exists(xml_path):
        with open(xml_path, 'w', encoding='utf-8') as f:
            f.write(requester.get(feed_url).text)
    # 读取本地XML文件
    if os.path.exists(video_xml_path):
        with open(video_xml_path, 'r', encoding='utf-8') as f:
            soup = bs4.BeautifulSoup(f, "xml")
    else:
        with open(xml_path, 'r', encoding='utf-8') as f:
            soup = bs4.BeautifulSoup(f, "xml")

    save_feed(soup, video_xml_path)

    # 遍历所有item并下载视频
    items = soup.find_all("item")
    for iii, item in enumerate(items):
        print('-' * 20, iii, '/', len(items), '-' * 20)

        enclosure = item.find('enclosure')
        if enclosure:
            print(str(enclosure))
            if enclosure['type'] == 'video/mp4' and enclosure['url'].startswith(BASE_URL):
                logger.info("Skipping video %s", item.find("link").text)
                continue
        
        # 获取视频的链接
        link = item.find("link").text
        logger.info("Downloading video %s", link)
        
        # 使用yt_dlp的YoutubeDL实例来下载视频信息，并尝试下载
        flag = False
        for i in range(3):
            try:
                with YoutubeDL(ydl_opts) as ydl:
                    info_dict = ydl.extract_info(link, download=True)
            except Exception:
                logger.error("Failed to download video %s, retrying...", link)
                continue
            flag = True
            time.sleep(3 + random.random() * 2)
            break
        if not flag:
            logger.error("Failed to download video %s", link)
            continue
        
        if info_dict is None:
            logger.error("Failed to download video %s", link)
            continue
        
        video_id = info_dict.get('id')
        uploader_id = info_dict.get('uploader_id')
        
        assert video_id is not None
        assert uploader_id is not None

        # 构建视频文件的URL
        url = '{}/{}/{}.mp4'.format(BASE_URL, uploader_id, video_id)
        # 更新或创建enclosure标签
        enclosure = item.find('enclosure')
        if enclosure:
            enclosure['url'] = url
            enclosure['type'] = 'video/mp4'
        else:
            new_enclosure = soup.new_tag('enclosure', url=url, type='video/mp4')
            item.append(new_enclosure)
        
        # 更新itunes:duration标签
        if not item.find('itunes:duration'):
            duration = info_dict.get('duration')
            if duration:
                new_duration = soup.new_tag('itunes:duration')
                new_duration.string = str('{:02d}:{:02d}:{:02d}'.format(int(duration // 3600), int(duration % 3600 // 60), int(duration % 60)))
                item.append(new_duration)

        if not item.find('itunes:image'):
            image = info_dict.get('thumbnail')
            if image:
                new_image = soup.new_tag('itunes:image', href=image)
                item.append(new_image)

        save_feed(soup, video_xml_path)

# 示例调用
if __name__ == "__main__":
    # 创建请求会话
    session = requests.Session()
    # 调用下载函数
    # download_videos("xxx", "https://www.youtube.com/feeds/videos.xml?channel_id=xxx", session, ydl_opts)
