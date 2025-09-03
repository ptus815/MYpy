# -*- coding: utf-8 -*-
# by @ao - 91nt 爬虫插件
import json
import re
import sys
from urllib.parse import urljoin, urlencode
from requests import Session
from pyquery import PyQuery as pq

sys.path.append('..')
from base.spider import Spider  # noqa: E402


class Spider(Spider):
    def init(self, extend=""):
        try:
            self.proxies = json.loads(extend) if extend else {}
        except Exception:
            self.proxies = {}
        if isinstance(self.proxies, dict) and 'proxy' in self.proxies:
            self.proxies = self.proxies['proxy']
        # 兼容 http/https 代理前缀
        self.proxies = {
            k: (v if isinstance(v, str) and v.startswith('http') else f'http://{v}')
            for k, v in self.proxies.items()
        }

        self.host = 'https://91nt.com'
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:142.0) Gecko/20100101 Firefox/142.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }

        self.session = Session()
        self.session.headers.update(self.headers)
        if isinstance(self.proxies, dict) and self.proxies:
            self.session.proxies.update(self.proxies)

    def getName(self):
        return '91nt'

    def isVideoFormat(self, url):
        return isinstance(url, str) and ('.m3u8' in url or url.endswith('.mp4') or '.mp4' in url)

    def manualVideoCheck(self):
        return True

    def destroy(self):
        try:
            self.session.close()
        except Exception:
            pass

    def _getpq(self, path_or_url=''):
        url = path_or_url if path_or_url.startswith('http') else urljoin(self.host, path_or_url)
        try:
            resp = self.session.get(url, timeout=15)
            resp.encoding = 'utf-8' if resp.encoding in (None, 'ISO-8859-1') else resp.encoding
            return pq(resp.text)
        except Exception:
            return pq('')

    def _parse_vlist(self, root_sel):
        vlist = []
        for item in root_sel.items():
            try:
                link = item('a').eq(0)
                href = link.attr('href') or ''
                if not href:
                    continue
                title_link = item('a').eq(1) if item('a').length > 1 else link
                name = title_link.text().strip() or link.text().strip()
                img = item('img').eq(0)
                pic = (img.attr('data-src') or img.attr('src') or '').strip()
                if pic and not pic.startswith('http'):
                    pic = urljoin(self.host, pic)
                # 时长在封面底部的小块里
                duration = item('.text-sm').text().strip() if item('.text-sm').length else ''

                vlist.append({
                    'vod_id': href if href.startswith('http') else urljoin(self.host, href),
                    'vod_name': name,
                    'vod_pic': pic,
                    'vod_year': '',
                    'vod_remarks': duration,
                    'style': {'ratio': 1.78, 'type': 'rect'}
                })
            except Exception:
                continue
        return vlist

    def homeContent(self, filter):
        cateManual = {
           
            '精选G片': '/videos/all/watchings',
            '男同黑料': '/posts/category/all',
            '热搜词': '/hot/1',
            '鲜肉薄肌': '/videos/category/xrbj',
            '无套内射': '/videos/category/wtns',
            '制服诱惑': '/videos/category/zfyh',
            '耽美天菜': '/videos/category/dmfj',
            '肌肉猛男': '/videos/category/jrmn',
            '日韩GV': '/videos/category/rhgv',
            '欧美巨屌': '/videos/category/omjd',
            '多人群交': '/videos/category/drqp',
            '口交颜射': '/videos/category/kjys',
        }
        classes = [{'type_name': k, 'type_id': v} for k, v in cateManual.items()]

        doc = self._getpq('/')
        vlist = self._parse_vlist(doc('div.video-item'))
        return {'class': classes, 'filters': {}, 'list': vlist}

    def categoryContent(self, tid, pg, filter, extend):
        try:
            page = int(pg) if isinstance(pg, str) else (pg or 1)
        except Exception:
            page = 1
        url = tid if tid.startswith('http') else urljoin(self.host, tid)
        if page and page > 1:
            joiner = '&' if ('?' in url) else '?'
            url = f"{url}{joiner}page={page}"
        doc = self._getpq(url)
        vlist = self._parse_vlist(doc('div.video-item'))
        return {'list': vlist, 'page': str(page), 'pagecount': 9999, 'limit': 90, 'total': 999999}

    def searchContent(self, key, quick, pg="1"):
        try:
            page = int(pg) if isinstance(pg, str) else (pg or 1)
        except Exception:
            page = 1
        # 站点的结构允许 /videos/search/{kw}
        path = f"/videos/search/{key}"
        url = urljoin(self.host, path)
        if page and page > 1:
            url = f"{url}?{urlencode({'page': page})}"
        doc = self._getpq(url)
        vlist = self._parse_vlist(doc('div.video-item'))
        return {'list': vlist, 'page': str(page)}

    def detailContent(self, ids):
        # 详情页中可直接在源码中用正则提取 data-url="...m3u8"
        url = ids[0]
        d = self._getpq(url)
        title = d('h1').text().strip() or d('h1.title-detail').text().strip() or ''

        # 尝试直接通过正则从页面源码中抓取 data-url
        try:
            # 直接请求文本
            resp = self.session.get(url, timeout=15)
            html = resp.text
        except Exception:
            html = d.html() or ''

        video_urls = []
        for m in re.finditer(r'data-url\s*=\s*"([^"]+\.m3u8[^"]*)"', html):
            play = m.group(1)
            if play and play.startswith('http'):
                video_urls.append(play)
        # 兜底：有些详情里也可能嵌在列表块
        if not video_urls:
            data_url = d('.poster').attr('data-url') or ''
            if data_url and data_url.startswith('http'):
                video_urls.append(data_url)

        video_urls = list(dict.fromkeys(video_urls))  # 去重并保持顺序
        if not video_urls:
            # 若未解析到直链，回退为原页面链接交由解析
            video_urls = [url]

        play_from = '91nt'
        # 只取第一个视频链接，不合并多条线路
        play_url = video_urls[0] if video_urls else url

        vod = {
            'vod_name': title or '91nt',
            'type_name': '',
            'vod_content': '91nt',
            'vod_play_from': play_from,
            'vod_play_url': play_url
        }
        return {'list': [vod]}

    def playerContent(self, flag, id, vipFlags):
        play_url = id
        if self.isVideoFormat(play_url):
            return {
                'parse': 0,
                'url': play_url,
                'header': {
                    'User-Agent': self.headers['User-Agent'],
                    'Referer': self.host,
                }
            }
        # 不是直链时，交由外部解析
        return {
            'parse': 1,
            'url': play_url,
            'header': {
                'User-Agent': self.headers['User-Agent'],
                'Referer': self.host,
            }
        }

    def localProxy(self, param):
        return None


