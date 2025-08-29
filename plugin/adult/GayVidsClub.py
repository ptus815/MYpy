# -*- coding: utf-8 -*-
# by @ao
import json
import sys
import re
from base64 import b64decode, b64encode
from urllib.parse import urlparse, urljoin, quote
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
        if isinstance(self.proxies, dict) and 'proxy' in self.proxies:
            self.proxies = self.proxies['proxy']
        self.proxies = {k: f'http://{v}' if isinstance(v, str) and not v.startswith('http') else v for k, v in self.proxies.items()}
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:142.0) Gecko/20100101 Firefox/142.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.3,en;q=0.2',
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

    def destroy(self):
        pass

    def homeContent(self, filter):
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
        classes = [{'type_name': k, 'type_id': v} for k, v in cateManual.items()]
        return {'class': classes, 'filters': {}}

    def homeVideoContent(self):
        data = self.getpq()
        vlist = self.getlist(data("article"))
        if not vlist:
            data = self.getpq('/all-gay-porn/')
            vlist = self.getlist(data("article"))
        if not vlist:
            try:
                rss = self.session.get(f'{self.host}/feed', timeout=15).text
                d = pq(rss)
                vlist = [{'vod_id': it('link').text().strip(),
                          'vod_name': it('title').text().strip(),
                          'vod_pic': re.search(r'<img[^>]+src=["\']([^"\']+)["\']', it('description').text() or '', re.I).group(1) if re.search(r'<img[^>]+src=["\']([^"\']+)["\']', it('description').text() or '', re.I) else '',
                          'vod_year': '',
                          'vod_remarks': '',
                          'style': {'ratio': 1.33, 'type': 'rect'}} for it in d('item').items() if it('link').text().strip() and it('title').text().strip()]
            except Exception as e:
                print(f'RSS解析失败: {e}')
        return {'list': vlist}

    def categoryContent(self, tid, pg, filter, extend):
        result = {'page': pg, 'pagecount': 9999, 'limit': 90, 'total': 999999}
        url = tid if pg == 1 else f"{tid}page/{pg}/"
        data = self.getpq(url)
        result['list'] = self.getlist(data("article"))
        return result

    def extract_m3u8_from_iframe(self, iframe_url, referer_url):
        """
        从 iframe 页面提取 .m3u8 链接，基于截图中的模式
        """
        headers = {
            'User-Agent': self.headers['User-Agent'],
            'Referer': referer_url,  # 动态设置为父页面 Referer
            'Accept': '*/*'
        }
        try:
            response = self.session.get(iframe_url, headers=headers, timeout=15)
            if response.status_code != 200:
                print(f"Failed to fetch iframe: {iframe_url}, status: {response.status_code}")
                return None
            soup = pq(response.text)
            
            scripts = soup('script')
            for script in scripts.items():
                if not script.text():
                    continue
                js_code = script.text()
                
                m3u8_match = re.search(
                    r'https://mivalyo\.com/stream/[a-zA-Z0-9-]+/[a-zA-Z0-9-]+/\d+/[a-zA-Z0-9]+/master\.m3u8',
                    js_code
                )
                if m3u8_match:
                    url = m3u8_match.group(0)
                    print(f"Found m3u8 via regex: {url}")
                    return url
                
                base64_matches = re.findall(r'atob\("([^"]+)"\)', js_code)
                for encoded in base64_matches:
                    try:
                        url = b64decode(encoded).decode('utf-8')
                        if '.m3u8' in url:
                            print(f"Found m3u8 via Base64: {url}")
                            return url
                    except:
                        continue
        except Exception as e:
            print(f"Error parsing iframe: {e}")
        return None

    def detailContent(self, ids):
        data = self.getpq(ids[0])
        
        title = data('h1').text().strip()
        info_text = data('.entry-meta, .post-meta').text().strip() or ''
        views_text = data('text:contains("views")').parent().text().strip() or ''
        tags = [tag.text().strip() for tag in data('.entry-tags a, .post-tags a, a[href*="/tag/"]').items() if tag.text().strip()]
        
        iframe_src = data('iframe').attr('src') or ''
        if not iframe_src:
            for attr in ['data-src', 'data-frame', 'data-iframe']:
                iframe_src = data(f'[{attr}]').attr(attr) or ''
                if iframe_src:
                    break
        if not iframe_src:
            scripts = data('script')
            for script in scripts.items():
                script_text = script.text()
                if script_text and 'iframe' in script_text and 'src' in script_text:
                    iframe_match = re.search(r'iframe.*?src=["\'](https?://[^"\']+mivalyo\.com[^"\']*)["\']', script_text, re.I)
                    if iframe_match:
                        iframe_src = iframe_match.group(1)
                        break
        if iframe_src and not iframe_src.startswith('http'):
            iframe_src = urljoin(self.host, iframe_src)

        m3u8_url = self.extract_m3u8_from_iframe(iframe_src, ids[0]) if iframe_src else None
        play_urls = []
        if m3u8_url:
            play_urls.append(f"播放${self.e64(f'{m3u8_url}@@@@{iframe_src}')}")
            vod_play_from = 'mivalyo'
        else:
            play_urls.append(f"播放${self.e64(f'{iframe_src}@@@@{iframe_src}')}")
            vod_play_from = 'mivalyo'

        vod = {
            'vod_name': title,
            'vod_content': ' | '.join(filter(None, [f"信息: {info_text}" if info_text else '', f"观看: {views_text}" if views_text else '', f"标签: {', '.join(tags)}" if tags else ''])),
            'vod_tag': ', '.join(tags) if tags else "GayVidsClub",
            'vod_play_from': vod_play_from,
            'vod_play_url': '#'.join(play_urls)
        }
        return {'list': [vod]}

    def searchContent(self, key, quick, pg="1"):
        url = f"/?s={key}" if pg == 1 else f"/page/{pg}/?s={key}"
        data = self.getpq(url)
        return {'list': self.getlist(data("article")), 'page': pg}

    def playerContent(self, flag, id, vipFlags):
        ids = self.d64(id).split('@@@@')
        play_url = ids[0]
        referer_url = ids[1] if len(ids) > 1 else ids[0]
        
        # 如果URL不是已知的视频格式，则设置parse标志让播放器APP来解析
        should_parse = 1 if not self.isVideoFormat(play_url) else 0
        
        headers = {
            'User-Agent': self.headers['User-Agent'],
            'Referer': referer_url,
            'Accept': '*/*',
            'Host': urlparse(play_url).netloc
        }
        return {'parse': should_parse, 'url': play_url, 'header': headers}

    def localProxy(self, param):
        url = self.d64(param['url'])
        if param.get('type') == 'm3u8':
            return self.m3Proxy(url)
        return self.tsProxy(url)

    def e64(self, text):
        try:
            return b64encode(text.encode('utf-8')).decode('utf-8')
        except Exception as e:
            print(f"Base64编码错误: {e}")
            return ""

    def d64(self, encoded_text):
        try:
            return b64decode(encoded_text.encode('utf-8')).decode('utf-8')
        except Exception as e:
            print(f"Base64解码错误: {e}")
            return ""

    def getlist(self, data):
        vlist = []
        for i in data.items():
            try:
                link_elem = i('h3 a, h2 a, h1 a, .entry-title a').eq(0)
                if not link_elem:
                    continue
                vod_id = link_elem.attr('href').strip()
                vod_name = link_elem.text().strip()
                if not vod_id or not vod_name:
                    continue
                
                img_elem = i('figure img').eq(0)
                vod_pic = img_elem.attr('src') or img_elem.attr('data-src') or img_elem.attr('data-original') or img_elem.attr('data-thumb') or img_elem.attr('data-lazy-src') or ''
                if not vod_pic and img_elem.attr('srcset'):
                    vod_pic = img_elem.attr('srcset').split(',')[0].split(' ')[0]
                if vod_pic and not vod_pic.startswith('http'):
                    vod_pic = urljoin(self.host, vod_pic)
                
                vod_year = next((line.strip() for line in i('figure').text().strip().split('\n') if line.strip() and not line.startswith('▶') and len(line) > 1), '')
                vod_remarks = i('time, .entry-meta a[href*="/202"], a[href*="/202"]').eq(0).text().strip() or i('time').attr('datetime', '').split('T')[0]
                
                vlist.append({
                    'vod_id': vod_id,
                    'vod_name': vod_name,
                    'vod_pic': vod_pic,
                    'vod_year': vod_year,
                    'vod_remarks': vod_remarks,
                    'style': {'ratio': 1.33, 'type': 'rect'}
                })
            except Exception as e:
                print(f"解析视频信息失败: {e}")
        return vlist

    def getpq(self, path=''):
        h = '' if path.startswith('http') else self.host
        try:
            response = self.session.get(f'{h}{path}', timeout=15)
            response.encoding = 'utf-8' if response.encoding == 'ISO-8859-1' else response.encoding
            return pq(response.text)
        except Exception as e:
            print(f"获取页面失败: {e}")
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
                if '#EXT' not in string:
                    if 'http' not in string:
                        domain = last_r if string.count('/') < 2 else durl
                        string = domain + ('' if string.startswith('/') else '/') + string
                    lines[index] = self.proxy(string, string.split('.')[-1].split('?')[0])
            
            data = '\n'.join(lines)
            return [200, "application/vnd.apple.mpegurl", data]
        except Exception as e:
            print(f"M3U8代理失败: {e}")
            return [500, "text/plain", f"Error: {e}"]

    def tsProxy(self, url):
        try:
            data = requests.get(url, headers=self.headers, proxies=self.proxies, stream=True, timeout=10)
            return [200, data.headers.get('Content-Type', 'application/octet-stream'), data.content]
        except Exception as e:
            print(f"TS代理失败: {e}")
            return [500, "text/plain", f"Error: {e}"]

    def proxy(self, data, type='img'):
        if data and self.proxies:
            return f"{self.getProxyUrl()}&url={self.e64(data)}&type={type}"
        return data
