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
        self.session.headers.update(self.headers)
        self.session.proxies.update(self.proxies)

    def getName(self):
        return "GayVidsClub"

    def isVideoFormat(self, url):
        return '.m3u8' in url or '.mp4' in url

    def manualVideoCheck(self):
        return True

    def destroy(self):
        pass

    def getpq(self, path=''):
        url = path if path.startswith('http') else self.host + path
        try:
            resp = self.session.get(url, timeout=15)
            resp.encoding = 'utf-8' if resp.encoding == 'ISO-8859-1' else resp.encoding
            return pq(resp.text)
        except Exception as e:
            print(f"获取页面失败: {e}")
            return pq("")

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
                vod_pic = img_elem.attr('src') or img_elem.attr('data-src') or img_elem.attr('data-original') or ''
                if vod_pic and not vod_pic.startswith('http'):
                    vod_pic = urljoin(self.host, vod_pic)
                # 日期（如果有）
                vod_year = i('.entry-date').text().strip() if i('.entry-date') else ''
                vlist.append({
                    'vod_id': b64encode(vod_url.encode('utf-8')).decode('utf-8'),
                    'vod_name': vod_name,
                    'vod_pic': vod_pic,
                    'vod_year': vod_year,
                    'vod_remarks': '',
                    'style': {'ratio': 1.33, 'type': 'rect'}
                })
            except Exception as e:
                print(f"解析视频信息失败: {e}")
        return vlist

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
        data = self.getpq('/all-gay-porn/')
        vlist = self.getlist(data('article'))
        if not vlist:  # RSS 回退
            try:
                rss = self.session.get(f'{self.host}/feed', timeout=15).text
                d = pq(rss)
                vlist = [{'vod_id': b64encode(it('link').text().strip().encode('utf-8')).decode('utf-8'),
                          'vod_name': it('title').text().strip(),
                          'vod_pic': re.search(r'<img[^>]+src=["\']([^"\']+)["\']', it('description').text() or '', re.I).group(1) if re.search(r'<img[^>]+src=["\']([^"\']+)["\']', it('description').text() or '', re.I) else '',
                          'vod_year': '',
                          'vod_remarks': '',
                          'style': {'ratio': 1.33, 'type': 'rect'}} for it in d('item').items() if it('link').text().strip() and it('title').text().strip()]
            except Exception as e:
                print(f'RSS解析失败: {e}')
        return {'class': classes, 'filters': {}, 'list': vlist}

    def categoryContent(self, tid, pg, filter, extend):
        url = tid if pg == 1 else f"{tid}page/{pg}/"
        data = self.getpq(url)
        vlist = self.getlist(data('article'))
        return {'page': pg, 'pagecount': 9999, 'limit': 90, 'total': 999999, 'list': vlist}

    def searchContent(self, key, quick, pg="1"):
        url = f"/?s={key}" if pg == "1" else f"/page/{pg}/?s={key}"
        data = self.getpq(url)
        vlist = self.getlist(data('article'))
        return {'list': vlist, 'page': pg}

    def detailContent(self, ids):
        url = b64decode(ids[0]).decode('utf-8')
        data = self.getpq(url)
        title = data('h1').text().strip() or '无标题'
        iframe_src = data('iframe').attr('src') or ''
        if not iframe_src:
            for attr in ['data-src', 'data-frame', 'data-iframe']:
                iframe_src = data(f'[{attr}]').attr(attr) or ''
                if iframe_src:
                    break
        if not iframe_src:
            iframe_src = url
        if not iframe_src.startswith('http'):
            iframe_src = urljoin(self.host, iframe_src)

        # 简介（正文内容）
        vod_content = data('.entry-content p').text().strip() if data('.entry-content p') else ''

        # 日期
        vod_year = data('.entry-date').text().strip() if data('.entry-date') else ''

        vod_play_url = b64encode(iframe_src.encode('utf-8')).decode('utf-8')
        vod = {
            'vod_name': title,
            'vod_pic': data('article img').attr('src') or '',
            'vod_year': vod_year,
            'vod_content': vod_content,
            'vod_play_from': 'Push',
            'vod_play_url': f'播放${vod_play_url}'
        }
        return {'list': [vod]}

    def playerContent(self, flag, id, vipFlags):
        play_url = b64decode(id.encode('utf-8')).decode('utf-8')
        return {
            'parse': 1,
            'url': play_url,
            'header': {
                'User-Agent': self.headers['User-Agent'],
                'Referer': self.host
            }
        }
