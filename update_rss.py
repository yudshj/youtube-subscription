import datetime
import http.cookiejar
import requests
import http
import bs4
import os
import sys
from utils import PROXY, OUTPUT_DIR, SUBSCRIBTIONS_LIST, COOKIEFILE, ydl_opts, logger, sort_by_published_date

# 如果命令行参数提供了订阅列表，则使用该列表
if len(sys.argv) > 1 and sys.argv[1]:
    SUBSCRIBTIONS_LIST = [sys.argv[1]]

def main():
    # 创建一个会话对象，用于保持会话状态
    requester = requests.Session()
    # 更新会话的cookie
    requester.cookies.update(http.cookiejar.MozillaCookieJar(COOKIEFILE))
    # 设置代理
    requester.proxies.update({"http": PROXY, "https": PROXY})

    # 遍历订阅列表并下载视频
    for name, feed_url in SUBSCRIBTIONS_LIST:
        update_rss(name, feed_url, requester, ydl_opts)

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

def update_rss(name: str, feed_url: str, requester: requests.Session, ydl_opts: dict):
    logger.info(f"Downloading videos from {name} feed")

    # 从URL获取最新的XML数据
    response = requester.get(feed_url)
    soup_new = bs4.BeautifulSoup(response.text, "xml")
    
    # 构建本地XML文件路径
    xml_path = os.path.join(OUTPUT_DIR, "@" + name + ".xml")

    # 读取本地XML文件
    with open(xml_path, 'r') as f:
        soup = bs4.BeautifulSoup(f, "xml")

    # 获取旧RSS feed中的所有链接
    old_soup_item_link_set = set(item.find("link").text for item in soup.find_all("item"))

    # 获取旧RSS feed中的channel元素
    soup_old_channel = soup.find("channel")
    assert soup_old_channel is not None
    # 将新RSS feed中的item添加到旧RSS feed中
    for i, entry in enumerate(soup_new.find_all("entry")):
        # import IPython
        # IPython.embed()
        # exit()
        link = entry.find("link").attrs['href']
        if link not in old_soup_item_link_set:
            logger.info(f"Inserting new video: {entry.find('media:title').text}")
            # create new item
            item = soup.new_tag("item")
            _title = soup.new_tag("title")
            _title.string = entry.find("media:title").text

            _description = soup.new_tag("description")
            _description.string = entry.find("media:description").text

            _link = soup.new_tag("link")
            _link.string = link

            _guid = soup.new_tag("guid", isPermaLink="false")
            _guid.string = link
            _pubDate = soup.new_tag("pubDate")
            __date = entry.find("published").text
            __date = datetime.datetime.strptime(__date, "%Y-%m-%dT%H:%M:%S+00:00")
            __date = __date.strftime('%a, %d %b %Y %H:%M:%S GMT')
            _pubDate.string = __date
            _author = soup.new_tag("author")
            _author.string = entry.find("author").find("name").text.strip()
            _enclosure = soup.new_tag("enclosure", url=entry.find("media:thumbnail").attrs['url'], type="image/jpeg")

            item.append(_title)
            item.append(_description)
            item.append(_link)
            item.append(_guid)
            item.append(_pubDate)
            item.append(_author)
            item.append(_enclosure)

            # add item to channel
            soup_old_channel.insert(10 + i, item)
    
    # import IPython
    # IPython.embed()
    # exit()
    # 保存新的RSS feed
    sort_by_published_date(soup_old_channel)
    save_feed(soup, xml_path)


if __name__ == "__main__":
    main()
