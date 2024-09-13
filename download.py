import datetime
import http.cookiejar
import logging
import requests
import http
import bs4
import os
# import sys
import json
from yt_dlp import YoutubeDL
from utils import PROXY, OUTPUT_DIR, BASE_URL, SUBSCRIBTIONS_LIST, COOKIEFILE, logger, ydl_opts

# # 如果命令行参数提供了订阅列表，则使用该列表
# if len(sys.argv) > 1 and sys.argv[1]:
#     SUBSCRIBTIONS_LIST = [sys.argv[1]]

def main():
    # 创建一个会话对象，用于保持会话状态
    requester = requests.Session()
    # 更新会话的cookie
    requester.cookies.update(http.cookiejar.MozillaCookieJar(COOKIEFILE))
    # 设置代理
    requester.proxies.update({"http": PROXY, "https": PROXY})

    # 遍历订阅列表并下载视频
    for name, feed_url in SUBSCRIBTIONS_LIST:
        download_videos(name, feed_url, requester, ydl_opts)

def save_feed(soup: bs4.BeautifulSoup, xml_path: str):
    # 将RSS feed保存到文件
    # Get the current date and time
    current_date = datetime.datetime.now(datetime.timezone.utc)

    # Format the current date and time to the desired format
    formatted_date = current_date.strftime('%a, %d %b %Y %H:%M:%S GMT')

    a = soup.find_all('lastBuildDate')

    if a:
        a[0].string = formatted_date

    with open(xml_path, 'w', encoding='utf-8') as f:
        f.write(str(soup))

def download_videos(name: str, feed_url: str, requester: requests.Session, ydl_opts: dict):
    # 构建本地XML文件路径
    xml_path = os.path.join(OUTPUT_DIR, '@' + name + '.xml')
    # 如果本地文件不存在，则从URL获取并保存
    if not os.path.exists(xml_path):
        with open(xml_path, 'w', encoding='utf-8') as f:
            f.write(requester.get('https://rsshub.app/youtube/user/@' + name).text)
    # 读取本地XML文件
    with open(xml_path, 'r', encoding='utf-8') as f:
        soup = bs4.BeautifulSoup(f, "xml")

    save_feed(soup, xml_path)

    rss_tag = soup.rss
    if not rss_tag:
        raise ValueError("RSS tag not found")
    rss_tag['xmlns:atom'] = "http://www.w3.org/2005/Atom"
    rss_tag['xmlns:itunes'] = "http://www.itunes.com/dtds/podcast-1.0.dtd"
    rss_tag['xmlns:content'] = "http://purl.org/rss/1.0/modules/content/"
    rss_tag['xmlns:podcast'] = "https://podcastindex.org/namespace/1.0"

    save_feed(soup, xml_path)

    # 遍历所有item并下载视频
    items = soup.find_all("item")
    # 遍历所有RSS feed中的item（视频条目）
    for iii, item in enumerate(items):
        print('-' * 20, iii, '/', len(items), '-' * 20)
        
        # # 获取每个item的描述文本
        # description = item.find("description").text
        # # 检查视频是否已经标记为【已缓存】
        # if description.startswith(SAVED_TAG):
        #     # 如果已缓存，则跳过此视频，并记录跳过的信息
        #     logger.info("Skipping video %s", item.find("link").text)
        #     continue  # 继续处理下一个item

        enclosure = item.find('enclosure')
        if enclosure:
            if enclosure['type'] == 'audio/mpeg' and enclosure['url'].startswith(BASE_URL):
                logger.info("Skipping video %s", item.find("link").text)
                continue
        
        # 获取视频的链接
        link = item.find("link").text
        # 记录即将下载的视频链接
        logger.info("Downloading video %s", link)
        
        # 使用yt_dlp的YoutubeDL实例来下载视频信息，并尝试下载
        with YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(link, download=True)
        
        # 检查是否成功获取视频信息
        if info_dict is None:
            # 如果没有成功获取视频信息，记录错误并继续处理下一个item
            logger.error("Failed to download video", link)
            continue
        
        # 从info_dict中获取视频ID和上传者ID
        video_id = info_dict.get('id')
        uploader_id = info_dict.get('uploader_id')
        
        # 确保获取到了视频ID和上传者ID
        assert video_id is not None
        assert uploader_id is not None

        # 构建音频文件的URL
        url = '{}/{}/{}.mp3'.format(BASE_URL, uploader_id, video_id)
        # 更新或创建enclosure标签
        enclosure = item.find('enclosure')
        if enclosure:
            enclosure['url'] = url
            enclosure['type'] = 'audio/mpeg'
        else:
            new_enclosure = soup.new_tag('enclosure', url=url, type='audio/mpeg')
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

        save_feed(soup, xml_path)

if __name__ == "__main__":
    main()
