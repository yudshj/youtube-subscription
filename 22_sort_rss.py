import datetime
import http
import bs4
import os
import sys
from utils import OUTPUT_DIR, SUBSCRIBTIONS_LIST, sort_by_published_date

# 如果命令行参数提供了订阅列表，则使用该列表
if len(sys.argv) > 1 and sys.argv[1]:
    SUBSCRIBTIONS_LIST = [sys.argv[1]]

def main():
    # 遍历订阅列表并下载视频
    for name, _feed_url in SUBSCRIBTIONS_LIST:
        update_rss(name)

def save_feed(soup: bs4.BeautifulSoup, xml_path: str):
    current_date = datetime.datetime.now(datetime.timezone.utc)
    formatted_date = current_date.strftime('%a, %d %b %Y %H:%M:%S GMT')
    a = soup.find_all('lastBuildDate')
    if a:
        a[0].string = formatted_date
    with open(xml_path, 'w') as f:
        f.write(str(soup))

def update_rss(name: str):
    xml_path = os.path.join(OUTPUT_DIR, "@" + name + ".xml")
    with open(xml_path, 'r') as f:
        soup = bs4.BeautifulSoup(f, "xml")
    soup_old_channel = soup.find("channel")
    assert soup_old_channel is not None
    sort_by_published_date(soup_old_channel)
    save_feed(soup, xml_path)

if __name__ == "__main__":
    main()
