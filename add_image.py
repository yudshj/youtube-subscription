import datetime
import time
import bs4
import os
from mutagen.mp3 import MP3
from pathlib import Path
from yt_dlp import YoutubeDL
import json

from utils import COOKIEFILE, PROXY, OUTPUT_DIR, ydl_opts


ydl = YoutubeDL(ydl_opts)

def save_feed(soup: bs4.BeautifulSoup, xml_path: str):
    # 将RSS feed保存到文件
    # Get the current date and time
    current_date = datetime.datetime.now(datetime.timezone.utc)

    # Format the current date and time to the desired format
    formatted_date = current_date.strftime('%a, %d %b %Y %H:%M:%S GMT')

    a = soup.find_all('lastBuildDate')

    if a:
        a[0].string = formatted_date

    with open(xml_path, 'w') as f:
        f.write(str(soup))

p = Path('downloads')
for xml in p.glob('*.xml'):
    soup = bs4.BeautifulSoup(xml.read_text(), 'xml')
    items = soup.find_all('item')
    for item in items:
        if not item.find('itunes:image'):
            url = item.find_all('link')[0].text
            info_dict = ydl.extract_info(url, download=False)
            time.sleep(1)
            assert info_dict is not None
            image = info_dict.get('thumbnail')
            if image:
                new_image = soup.new_tag('itunes:image', href=image)
                item.append(new_image)
                save_feed(soup, xml_path=xml.as_posix())

                