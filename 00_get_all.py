# yt-dlp --flat-playlist --print id https://www.youtube.com/@

import datetime
import os
import subprocess
import sys
import tempfile

import bs4
import yt_dlp

PREFIX = 'https://www.youtube.com/watch?v='
NAME = sys.argv[1]
try:
    PLAYLIST_URL = sys.argv[2]
except:  # noqa: E722
    PLAYLIST_URL = f'https://www.youtube.com/@{NAME}'

temp_filename = f"{NAME}.txt"
temp_filepath = tempfile.gettempdir() + '/' + temp_filename

print(temp_filepath)
print(temp_filepath)
print(temp_filepath)

def save(soup):
    with open(f'./downloads/@{NAME}.xml', 'w') as f:
        f.write(str(soup))

def main():
    with open(f'./downloads/@{NAME}.xml', 'r') as f:
        soup = bs4.BeautifulSoup(f, "xml")

    channel = soup.find("channel")

    if not os.path.exists(temp_filepath):
        # shell_command = f'yt-dlp --flat-playlist --print id https://www.youtube.com/@{NAME}'
        shell_command = f'yt-dlp --flat-playlist --print id {PLAYLIST_URL}'
        output = subprocess.check_output(shell_command, shell=True)
        input_fp = output.decode().split('\n')
        with open(temp_filepath, 'w') as f:
            f.write('\n'.join(input_fp))

    with open(temp_filepath, 'r') as fp:
        lines = fp.readlines()

    assert channel is not None
    soup_item_link_set = set(item.find("link").text for item in soup.find_all("item"))

    for i, line in enumerate(lines):
        print("PROGRESS: {}/{}".format(i, len(lines)))
        line = line.strip()
        if len(line) > 0:
            try:
                url = PREFIX + line
                if url in soup_item_link_set:
                    continue
                item = soup.new_tag("item")

                ytp = yt_dlp.YoutubeDL({
                    'skip_download': True,
                    'proxy': 'http://127.0.0.1:11632',
                    'cookiesfrombrowser': ['chrome']
                })
                info_dict = ytp.extract_info(url, download=False)
                ytp.close()
                assert info_dict is not None
                title = soup.new_tag("title")
                title.string = info_dict.get('title') # type: ignore
                description = soup.new_tag("description")
                description.string = info_dict.get('description') # type: ignore
                link = soup.new_tag("link")
                link.string = url
                guid = soup.new_tag("guid", isPermaLink="false")
                guid.string = url
                pubDate = soup.new_tag("pubDate")
                _timestamp = int(info_dict['timestamp'])
                # pubDate.string = _timestamp.strftime('%a, %d %b %Y %H:%M:%S GMT')
                pubDate.string = datetime.datetime.fromtimestamp(_timestamp, datetime.timezone.utc).strftime('%a, %d %b %Y %H:%M:%S GMT')
                author = soup.new_tag("author")
                author.string = info_dict.get('uploader').strip() # type: ignore
                enclosure = soup.new_tag("enclosure", type="image/jpeg", url=info_dict.get('thumbnail'))
                duration = soup.new_tag("itunes:duration")
                _dur = int(info_dict.get('duration')) # type: ignore
                duration.string = '{:02d}:{:02d}:{:02d}'.format(_dur // 3600, (_dur % 3600) // 60, _dur % 60)
                item.append(title)
                item.append(description)
                item.append(link)
                item.append(guid)
                item.append(pubDate)
                item.append(author)
                item.append(enclosure)
                # item.append(duration)
                channel.append(item)
                save(soup)
            except Exception as e:
                print(e)
                continue
    print(soup.prettify())
    save(soup)

if __name__ == '__main__':
    main()