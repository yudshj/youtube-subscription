from webdav4.client import Client
from yt_dlp import YoutubeDL
from utils import PROXY, WEBDAV_USER, WEBDAV_PASS, WEBDAV_HOST, WEBDAV_PATH

ydl_opts = {
    "cookiesfrombrowser": ['chrome'],
    "proxy": PROXY,
    "format": "bestaudio/best",
}

ydl = YoutubeDL(ydl_opts)

with open('youtube.com_cookies.txt', 'w', encoding='utf-8') as f:
    f.write('''# Netscape HTTP Cookie File
# http://curl.haxx.se/rfc/cookie_spec.html
# This is a generated file!  Do not edit.\n\n''')
    
    # Domain	Include subdomains	Path	Secure	Expiry	Name	Value
    for cookie in ydl.cookiejar:
        if 'youtube' in cookie.domain:
            cookie_secure = 'TRUE' if cookie.secure else 'FALSE'
            cookie_include_subdomains = 'TRUE' if cookie.domain.startswith('.') else 'FALSE'
            cookie_expire = cookie.expires if cookie.expires else 0
            f.write(f'{cookie.domain}\t{cookie_include_subdomains}\t{cookie.path}\t{cookie_secure}\t{cookie_expire}\t{cookie.name}\t{cookie.value}\n')  

client = Client(WEBDAV_HOST, auth=(WEBDAV_USER, WEBDAV_PASS))
client.upload_file('youtube.com_cookies.txt', WEBDAV_PATH, overwrite=True) # type: ignore