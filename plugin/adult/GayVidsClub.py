# -*- coding: utf-8 -*-
import json
import sys
import re
from base64 import b64decode, b64encode
from urllib.parse import urlparse, urljoin, quote
import requests
from pyquery import PyQuery as pq
from requests import Session
import jsbeautifier
import execjs
import subprocess

class Spider:
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
        self.headers.update({
            'origin': self.host, 
            'referer': f'{self.host}/',
            'host': 'gayvidsclub.com'
        })
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
        filters = {}
        for k in cateManual:
            classes.append({
                'type_name': k,
                'type_id': cateManual[k]
            })
        result['class'] = classes
        result['filters'] = filters
        return result

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
                vlist = []
                for it in d('item').items():
                    link = it('link').text().strip()
                    title = it('title').text().strip()
                    thumb = ''
                    desc = it('description').text()
                    m = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', desc or '', re.I)
                    if m:
                        thumb = m.group(1)
                    if link and title:
                        vlist.append({
                            'vod_id': link,
                            'vod_name': title,
                            'vod_pic': thumb,
                            'vod_year': '',
                            'vod_remarks': '',
                            'style': {'ratio': 1.33, 'type': 'rect'}
                        })
            except Exception as e:
                print(f'RSS解析失败: {e}')
        return {'list': vlist}

    def categoryContent(self, tid, pg, filter, extend):
        vdata = []
        result = {}
        result['page'] = pg
        result['pagecount'] = 9999
        result['limit'] = 90
        result['total'] = 999999
        if pg == 1:
            url = tid
        else:
            url = f"{tid}page/{pg}/"
        data = self.getpq(url)
        vdata = self.getlist(data("article"))
        result['list'] = vdata
        return result

    def extract_m3u8_from_iframe(self, iframe_url):
        """
        从 iframe 页面提取 .m3u8 链接，处理 JavaScript 混淆
        """
        headers = {
            'User-Agent': self.headers['User-Agent'],
            'Referer': self.host,
            'Accept': '*/*'
        }
        try:
            # 获取 iframe 页面
            response = self.session.get(iframe_url, headers=headers, timeout=15)
            if response.status_code != 200:
                print(f"Failed to fetch iframe: {iframe_url}")
                return None
            soup = pq(response.text)
            
            # 提取并格式化 JavaScript
            scripts = soup('script')
            for script in scripts.items():
                if not script.text():
                    continue
                js_code = jsbeautifier.beautify(script.text())
                
                # 1. 尝试提取 Base64 编码的 .m3u8
                base64_matches = re.findall(r'atob\("([^"]+)"\)', js_code)
                for encoded in base64_matches:
                    try:
                        url = b64decode(encoded).decode('utf-8')
                        if '.m3u8' in url:
                            print(f"Found m3u8 via Base64: {url}")
                            return url
                    except:
                        continue
                
                # 2. 尝试提取字符串数组中的 .m3u8
                array_matches = re.findall(r'var\s+\w+\s*=\s*\[(.*?)\]', js_code, re.DOTALL)
                for array in array_matches:
                    strings = re.findall(r'"([^"]+)"', array)
                    for s in strings:
                        try:
                            url = b64decode(s).decode('utf-8')
                            if '.m3u8' in url:
                                print(f"Found m3u8 via array Base64: {url}")
                                return url
                        except:
                            continue
                
                # 3. 尝试执行 JavaScript
                try:
                    ctx = execjs.compile(js_code)
                    for func_name in ['getM3U8', 'decode', 'hls_src', 'getHlsUrl', 'getUrl']:
                        try:
                            result = ctx.call(func_name)
                            if isinstance(result, str) and '.m3u8' in result:
                                print(f"Found m3u8 via JS execution: {result}")
                                return result
                        except:
                            continue
                except:
                    continue
            
            # 4. 检查可能的 API 请求
            api_matches = re.findall(r'["\'](https?://[^"\']+/api/[^"\']+)["\']', response.text)
            for api_url in api_matches:
                try:
                    api_response = self.session.get(api_url, headers=headers, timeout=10)
                    if api_response.status_code == 200:
                        data = api_response.json()
                        for key in ['url', 'm3u8_url', 'hls_url', 'source']:
                            if key in data and '.m3u8' in data[key]:
                                print(f"Found m3u8 via API: {data[key]}")
                                return data[key]
                except:
                    continue
        except Exception as e:
            print(f"Error parsing iframe: {e}")

        # 5. 使用 yt-dlp 作为备用
        print(f"Trying yt-dlp for {iframe_url}")
        try:
            command = [
                "yt-dlp",
                "-g",
                "--ignore-errors",
                "--no-warnings",
                "--referer", iframe_url,
                "--user-agent", self.headers['User-Agent'],
                iframe_url
            ]
            result = subprocess.run(command, capture_output=True, text=True)
            m3u8_urls = [line for line in result.stdout.splitlines() if ".m3u8" in line]
            if m3u8_urls:
                print(f"Found m3u8 via yt-dlp: {m3u8_urls[0]}")
                return m3u8_urls[0]
        except Exception as e:
            print(f"yt-dlp failed: {e}")

        return None

    def detailContent(self, ids):
        data = self.getpq(ids[0])
        title = data('h1').text().strip()
        info_text = data('.entry-meta, .post-meta').text().strip() or ''
        views_text = data('text:contains("views")').parent().text().strip() or ''
        tags = [tag.text().strip() for tag in data('.entry-tags a, .post-tags a, a[href*="/tag/"]').items() if tag.text().strip()]
        
        # 提取 iframe src（仅保留一种方法）
        iframe_src = data('iframe').attr('src') or ''
        if iframe_src and not iframe_src.startswith('http'):
            iframe_src = urljoin(self.host, iframe_src)

        # 提取 .m3u8 链接
        m3u8_url = self.extract_m3u8_from_iframe(iframe_src) if iframe_src else None
        play_urls = []
        if m3u8_url:
            play_urls.append(f"播放${self.e64(f'{m3u8_url}@@@@{iframe_src}')}")
            vod_play_from = 'filemoon'
        else:
            play_urls.append(f"播放${self.e64(f'{iframe_src}@@@@{ids[0]}')}")
            vod_play_from = 'filemoon'

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
        m3u8_url = ids[0]
        iframe_url = ids[1] if len(ids) > 1 else m3u8_url
        
        headers = {
            'User-Agent': self.headers['User-Agent'],
            'Referer': iframe_url,
            'Accept': '*/*',
            'Host': urlparse(m3u8_url).netloc
        }
        return {'parse': 0, 'url': m3u8_url, 'header': headers}

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
                link_elem = i('h3 a, h2 a, h1 a').eq(0)
                if not link_elem or len(link_elem) == 0:
                    link_elem = i('.entry-title a').eq(0)
                if not link_elem:
                    continue
                vod_id = (link_elem.attr('href') or '').strip()
                if not vod_id:
                    continue
                vod_name = link_elem.text().strip()
                
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
                
                figure_text = i('figure').text()
                category_text = ''
                if figure_text:
                    lines = figure_text.strip().split('\n')
                    for line in lines:
                        line = line.strip()
                        if line and not line.startswith('▶') and len(line) > 1:
                            category_text = line
                            break
                vod_year = category_text
                
                vod_remarks = ''
                time_elem = i('time, .entry-meta a[href*="/202"], a[href*="/202"]').eq(0)
                if time_elem:
                    vod_remarks = (time_elem.text() or '').strip()
                if not vod_remarks:
                    t = i('time').attr('datetime')
                    if t:
                        vod_remarks = t.strip().split('T')[0]
                
                if vod_id and vod_name:
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
                continue
        return vlist

    def getpq(self, path=''):
        h = '' if path.startswith('http') else self.host
        try:
            response = self.session.get(f'{h}{path}', timeout=15)
            if response.encoding == 'ISO-8859-1':
                response.encoding = 'utf-8'
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
        if data and len(self.proxies):
            return f"{self.getProxyUrl()}&url={self.e64(data)}&type={type}"
        return data
