import bs4
import os
from mutagen.mp3 import MP3
from pathlib import Path

p = Path('downloads')
for xml in p.glob('*.xml'):
    soup = bs4.BeautifulSoup(xml.read_text(), 'xml')
    items = soup.find_all('item')
    for item in items:
        url = item.find_all('enclosure')[0]['url']
        mp3_file = os.path.join('downloads', *url.split('/')[-2:])
        music = MP3(mp3_file)
        duration = music.info.length
        # format to hh:mm:ss
        fmt = '{:02d}:{:02d}:{:02d}'
        duration = fmt.format(int(duration // 3600), int(duration % 3600 // 60), int(duration % 60))
        aa = soup.new_tag('itunes:duration')
        aa.string = duration
        item.append(aa)
    with open(xml.name, 'w') as f:
        f.write(str(soup))