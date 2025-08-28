# -*- coding: utf-8 -*-
import json
import sys
import re
from base64 import b64decode, b64encode
from urllib.parse import urlparse, urljoin
import requests
from pyquery import PyQuery as pq
from requests import Session
sys.path.append('..')
from base.spider import Spider

class Spider(Spider):
    def init(self, extend=""):
        try:
            self.proxies = json.loads(extend) if extend else {}
        except:
            self.proxies = {}
        if isinstance(self.proxies, dict) and 'proxy' in self.proxies and isinstance(self.proxies['proxy'], dict):
            self.proxies = self.proxies['proxy']
        fixed = {}
        for k, v in (self.proxies or {}).items():
            if isinstance(v, str) and not v.startswith('http'):
                fixed[k] = f'http://{v}'
            else:
                fixed[k] = v
        self.proxies = fixed
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:142.0) Gecko/20100101 Firefox/142.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.3,en;q=0.2',
            'Referer': 'https://gayvidsclub.com/',
        }
        self.host = "https://gayvidsclub.com"
        self.session = Session()
        self.session.proxies.update(self.proxies)
        self.session.headers.update(self.headers)

    def getName(self):
        return "GayVidsClub"

    def isVideoFormat(self, url):
        return '.m3u8' in url or '.mp4' in url

    def manualVideoCheck(self):
        return True

    def homeContent(self, filter):
        result = {}
        cateManual = {
            "最新": "/all-gay-porn/",
            "COAT": "/all-gay-porn/coat/",
            "MEN'S RUSH.TV": "/all-gay-porn/mens-rush-tv/",
            "HUNK CHANNEL": "/all-gay-porn/hunk-channel/",
            "KO": "/all-gay-porn/ko/",
            "EXFEED": "/all-gay-porn/exfeed/",
            "BRAVO!": "/all-gay-porn/bravo/",
            "STR8BOYS": "/all-gay-porn/str8boys/",
            "G-BOT": "/all-gay-porn/g-bot/"
        }
        classes = []
        for k in cateManual:
            classes.append({
                'type_name': k,
                'type_id': cateManual[k]
            })
        result['class'] = classes
        result['filters'] = {}
        return result

    def homeVideoContent(self):
        data = self.getpq()
        vlist = self.getlist(data("article"))
        if not vlist:
            data = self.getpq('/all-gay-porn/')
            vlist = self.getlist(data("article"))
        return {'list': vlist}

    def categoryContent(self, tid, pg, filter, extend):
        result = {'page': pg, 'pagecount': 9999, 'limit': 90, 'total': 999999}
        url = tid if pg == 1 else f"{tid}page/{pg}/"
        data = self.getpq(url)
        result['list'] = self.getlist(data("article"))
        return result

    def detailContent(self, ids):
        data = self.getpq(ids[0])
        title = data('h1').text().strip()
        
        # 获取iframe src
        iframe_src = data('iframe').attr('src')
        if iframe_src and not iframe_src.startswith('http'):
            iframe_src = urljoin(self.host, iframe_src)
        
        # 从JavaScript中提取iframe URL（备用方法）
        if not iframe_src:
            scripts = data('script')
            for script in scripts.items():
                script_text = script.text()
                if script_text and 'iframe' in script_text:
                    iframe_match = re.search(r'src=["\'](https?://[^"\']+mivalyo\.com[^"\']*)["\']', script_text, re.IGNORECASE)
                    if iframe_match:
                        iframe_src = iframe_match.group(1)
                        break
        
        vod = {
            'vod_name': title,
            'vod_content': "GayVidsClub视频",
            'vod_tag': "GayVidsClub",
            'vod_play_from': 'GayVidsClub',
            'vod_play_url': ''
        }
        
        if iframe_src:
            vod['vod_play_from'] = 'mivalyo'
            vod['vod_play_url'] = f"播放${self.e64(iframe_src)}"
        
        return {'list': [vod]}

    def searchContent(self, key, quick, pg="1"):
        url = f"/?s={key}" if pg == 1 else f"/page/{pg}/?s={key}"
        data = self.getpq(url)
        return {'list': self.getlist(data("article")), 'page': pg}

    def playerContent(self, flag, id, vipFlags):
        iframe_url = self.d64(id)
        
        # 从iframe页面提取m3u8
        m3u8_url = self.extract_m3u8_from_iframe(iframe_url)
        
        if m3u8_url:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:142.0) Gecko/20100101 Firefox/142.0',
                'Referer': iframe_url,
                'Cookie': 'tsn=2',
                'Accept': '*/*',
                'Accept-Encoding': 'gzip, deflate, br, zstd',
                'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
                'Connection': 'keep-alive',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin',
                'Sec-GPC': '1',
                'TE': 'trailers',
                'Host': 'mivalyo.com'
            }
            return {'parse': 0, 'url': m3u8_url, 'header': headers}
        return {'parse': 0, 'url': ''}

    def localProxy(self, param):
        url = self.d64(param['url'])
        if param.get('type') == 'm3u8':
            return self.m3Proxy(url)
        else:
            return self.tsProxy(url)

    def e64(self, text):
        try:
            return b64encode(text.encode('utf-8')).decode('utf-8')
        except:
            return ""

    def d64(self, encoded_text):
        try:
            return b64decode(encoded_text.encode('utf-8')).decode('utf-8')
        except:
            return ""

    def getlist(self, data):
        vlist = []
        for i in data.items():
            try:
                link_elem = i('h3 a, h2 a, h1 a, .entry-title a').eq(0)
                if not link_elem:
                    continue
                vod_id = (link_elem.attr('href') or '').strip()
                vod_name = link_elem.text().strip()
                if not vod_id or not vod_name:
                    continue
                
                img_elem = i('figure img').eq(0)
                vod_pic = ''
                if img_elem:
                    vod_pic = (img_elem.attr('src') or '').strip()
                    if not vod_pic:
                        for attr in ['data-src', 'data-original', 'data-thumb', 'data-lazy-src']:
                            vod_pic = (img_elem.attr(attr) or '').strip()
                            if vod_pic:
                                break
                    if not vod_pic:
                        srcset = (img_elem.attr('srcset') or '').strip()
                        if srcset:
                            vod_pic = srcset.split(',')[0].split(' ')[0]
                    if vod_pic and not vod_pic.startswith('http'):
                        vod_pic = urljoin(self.host, vod_pic)
                
                vlist.append({
                    'vod_id': vod_id,
                    'vod_name': vod_name,
                    'vod_pic': vod_pic,
                    'vod_year': '',
                    'vod_remarks': '',
                    'style': {'ratio': 1.33, 'type': 'rect'}
                })
            except:
                continue
        return vlist

    def getpq(self, path=''):
        h = '' if path.startswith('http') else self.host
        try:
            response = self.session.get(f'{h}{path}', timeout=15)
            if response.encoding == 'ISO-8859-1':
                response.encoding = 'utf-8'
            return pq(response.text)
        except:
            return pq("")

    def m3Proxy(self, url):
        try:
            ydata = requests.get(url, headers=self.headers, proxies=self.proxies, allow_redirects=False, timeout=10)
            data = ydata.content.decode('utf-8')
            if ydata.headers.get('Location'):
                url = ydata.headers['Location']
                data = requests.get(url, headers=self.headers, proxies=self.proxies, timeout=10).content.decode('utf-8')
            
            lines = data.strip().split('\n')
            last_r = url[:url.rfind('/')]
            parsed_url = urlparse(url)
            durl = parsed_url.scheme + "://" + parsed_url.netloc
            
            for index, string in enumerate(lines):
                if '#EXT' not in string and 'http' not in string:
                    domain = last_r if string.count('/') < 2 else durl
                    string = domain + ('' if string.startswith('/') else '/') + string
                    lines[index] = self.proxy(string, string.split('.')[-1].split('?')[0])
            
            return [200, "application/vnd.apple.mpegurl", '\n'.join(lines)]
        except Exception as e:
            return [500, "text/plain", f"Error: {str(e)}"]

    def tsProxy(self, url):
        try:
            data = requests.get(url, headers=self.headers, proxies=self.proxies, stream=True, timeout=10)
            return [200, data.headers.get('Content-Type', 'application/octet-stream'), data.content]
        except Exception as e:
            return [500, "text/plain", f"Error: {str(e)}"]

    def proxy(self, data, type='img'):
        if data and len(self.proxies):
            return f"{self.getProxyUrl()}&url={self.e64(data)}&type={type}"
        else:
            return data 

    def extract_m3u8_from_iframe(self, iframe_url):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:142.0) Gecko/20100101 Firefox/142.0',
                'Referer': 'https://gayvidsclub.com/',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
                'Cookie': 'tsn=2'
            }
            
            r = self.session.get(iframe_url, headers=headers, timeout=15)
            html = r.text or ''
            
            # 查找JWPlayer配置中的m3u8地址
            patterns = [
                r'file["\']?\s*:\s*["\'](https?://[^"\']+\.m3u8[^"\']*)["\']',
                r'src["\']?\s*:\s*["\'](https?://[^"\']+\.m3u8[^"\']*)["\']',
                r'https?://[^\s"\']*mivalyo\.com[^\s"\']*stream[^\s"\']*\.m3u8[^\s"\']*'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, html, re.IGNORECASE)
                if matches:
                    return matches[0]
                    
            return ''
        except:
            return ''
