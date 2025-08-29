# -*- coding: utf-8 -*-
# by @ao
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

        self.cateManual = {
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

    def getName(self):
        return "GayVidsClub-Push"

    def getpq(self, path=''):
        url = path if path.startswith('http') else self.host + path
        try:
            resp = self.session.get(url, timeout=15)
            resp.encoding = 'utf-8' if resp.encoding == 'ISO-8859-1' else resp.encoding
            return pq(resp.text)
        except Exception as e:
            print(f"获取页面失败: {e}")
            return pq("")

    # 解析视频列表
    def getlist(self, selector):
        vlist = []
        for i in selector.items():
            try:
                link_elem = i('h3 a, h2 a, h1 a, .entry-title a').eq(0)
                if not link_elem:
                    continue
                vod_url = link_elem.attr('href').strip()
                vod_name = link_elem.text().strip()
                if not vod_url or not vod_name:
                    continue

                img_elem = i('figure img').eq(0)
                vod_pic = img_elem.attr('src') or img_elem.attr('data-src') or ''
                if vod_pic and not vod_pic.startswith('http'):
                    vod_pic = urljoin(self.host, vod_pic)
                vod_year = next((line.strip() for line in i('figure').text().split('\n') if line.strip()), '')
                vod_remarks = i('time').eq(0).text().strip() or ''

                # Base64 ID 包含原 URL，用于 Push Spider 解析
                vod_id = b64encode(f"{vod_url}@@@@{vod_url}".encode('utf-8')).decode('utf-8')

                vlist.append({
                    'vod_id': vod_id,
                    'vod_name': vod_name,
                    'vod_pic': vod_pic,
                    'vod_year': vod_year,
                    'vod_remarks': vod_remarks,
                    'style': {'ratio': 1.33, 'type': 'rect'}
                })
            except Exception as e:
                print(f"解析视频失败: {e}")
        return vlist

    # 首页分类
    def homeContent(self, filter):
        classes = [{'type_name': k, 'type_id': v} for k, v in self.cateManual.items()]
        data = self.getpq('/all-gay-porn/')
        vlist = self.getlist(data('article'))
        return {'class': classes, 'filters': {}, 'list': vlist}

    def categoryContent(self, tid, pg, filter, extend):
        url = tid if pg == 1 else f"{tid}page/{pg}/"
        data = self.getpq(url)
        vlist = self.getlist(data('article'))
        return {'page': pg, 'pagecount': 9999, 'limit': 90, 'total': 999999, 'list': vlist}

    def searchContent(self, key, quick, pg="1"):
        url = f"/?s={key}" if pg == "1" else f"/page/{pg}/?s={key}"
        data = self.getpq(url)
        vlist = self.getlist(data("article"))
        return {'list': vlist, 'page': pg}

    def extract_iframe_src(self, data):
        iframe_src = data('iframe').attr('src') or ''
        if not iframe_src:
            for attr in ['data-src', 'data-frame', 'data-iframe']:
                iframe_src = data(f'[{attr}]').attr(attr) or ''
                if iframe_src:
                    break
        if iframe_src and not iframe_src.startswith('http'):
            iframe_src = urljoin(self.host, iframe_src)
        return iframe_src

    # 详情页调用 Push Spider 解析多线路
    def detailContent(self, ids):
        video_url = b64decode(ids[0].encode('utf-8')).decode('utf-8').split('@@@@')[0]
        data = self.getpq(video_url)
        title = data('h1').text().strip() or '无标题'
        iframe_src = self.extract_iframe_src(data)
        play_url = iframe_src if iframe_src else video_url

        # 调用 Push Spider 解析
        try:
            from catvod_api import call_spider
            vod_json = call_spider('csp_Push', 'detailContent', [play_url])
        except Exception as e:
            print(f"调用 Push Spider 失败: {e}")
            vod_json = {'list':[{'vod_name': title, 'vod_play_from': '直连', 'vod_play_url': play_url}]}

        if 'list' in vod_json and len(vod_json['list'])>0:
            vod_json['list'][0]['vod_name'] = title

        return vod_json

    def playerContent(self, flag, id, vipFlags):
        ids = b64decode(id.encode('utf-8')).decode('utf-8').split('@@@@')
        play_url = ids[0]
        referer_url = ids[1] if len(ids)>1 else ids[0]
        return {
            'parse': 1,
            'url': play_url,
            'header': {
                'User-Agent': self.headers['User-Agent'],
                'Referer': referer_url,
                'Origin': self.host,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
                'Connection': 'keep-alive'
            }
        }

    def e64(self, text):
        try:
            return b64encode(text.encode('utf-8')).decode('utf-8')
        except:
            return ""

    def d64(self, text):
        try:
            return b64decode(text.encode('utf-8')).decode('utf-8')
        except:
            return ""

    def localProxy(self, param):
        url = self.d64(param['url'])
        if param.get('type') == 'm3u8':
            return self.m3Proxy(url)
        return self.tsProxy(url)

    def m3Proxy(self, url):
        try:
            resp = requests.get(url, headers=self.headers, proxies=self.proxies, allow_redirects=False, timeout=10)
            data = resp.content.decode('utf-8')
            if resp.headers.get('Location'):
                url = resp.headers['Location']
                data = requests.get(url, headers=self.headers, proxies=self.proxies, timeout=10).content.decode('utf-8')
            lines = data.strip().split('\n')
            last_r = url[:url.rfind('/')]
            parsed_url = urlparse(url)
            durl = parsed_url.scheme + "://" + parsed_url.netloc
            for idx, line in enumerate(lines):
                if '#EXT' not in line and 'http' not in line:
                    domain = last_r if line.count('/')<2 else durl
                    line = domain + ('' if line.startswith('/') else '/') + line
                lines[idx] = self.proxy(line, line.split('.')[-1].split('?')[0])
            return [200, "application/vnd.apple.mpegurl", '\n'.join(lines)]
        except Exception as e:
            return [500, "text/plain", f"Error: {e}"]

    def tsProxy(self, url):
        try:
            resp = requests.get(url, headers=self.headers, proxies=self.proxies, stream=True, timeout=10)
            return [200, resp.headers.get('Content-Type','application/octet-stream'), resp.content]
        except Exception as e:
            return [500, "text/plain", f"Error: {e}"]

    def proxy(self, data, type='img'):
        if data and self.proxies:
            return f"{self.getProxyUrl()}&url={self.e64(data)}&type={type}"
        return data
